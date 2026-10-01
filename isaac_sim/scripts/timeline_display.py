"""press_cp_main.usda의 Play/Pause/Stop 숫자 표시 구현."""
import asyncio
import json
from pathlib import Path
import sys
import time

from omni.behavior.scripting.core import BehaviorScript

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import display_playback
import press_cp_environment as geometry


class PressCpPlayBehavior(BehaviorScript):
    def on_init(self):
        self._prepare_task = None
        self.controller = None
        self.playing = False
        self.error = None
        self._next_index = 0
        self._deadline = 0
        self.last_update_time = None
        self.config = display_playback.read_config()
        self.cfg = geometry.read_config()
        sequence=json.loads((geometry.ROOT/"config/dataset_capture.json").read_text(encoding="utf-8"))
        self.values = display_playback.SequentialValues(sequence["sequence"])

    async def _prepare(self):
        from pxr import Usd
        import omni.kit.app
        from omni.kit.viewport.utility import get_active_viewport
        self.settings.set("/app/useFabricSceneDelegate", True)
        # 현재 Stage와 카메라를 유지하며 실행용 Mesh만 SessionLayer에 추가한다.
        with Usd.EditContext(self.stage, self.stage.GetSessionLayer()):
            display_playback.author_live_geometry(self.stage,self.cfg)
        viewport=get_active_viewport()
        if viewport:
            await asyncio.wait_for(viewport.wait_for_rendered_frames(10),120)
        else:
            for _ in range(10): await omni.kit.app.get_app().next_update_async()
        self.controller=display_playback.FabricDisplay(self.usd_context,self.cfg)
        self._apply(0)

    def _apply(self, index):
        from pxr import Usd
        frame=self.values.frame(index,self.cfg)
        self.controller.apply(frame)
        # Fabric 표시값과 조회용 문자열을 같은 갱신에서 연결한다.
        with Usd.EditContext(self.stage,self.stage.GetSessionLayer()):
            for row in frame["slots"]:
                self.stage.GetPrimAtPath(f"/World/Cabinet/Panels/{row['slot_id']}").SetCustomDataByKey("display_text",row["text"])
        self._next_index=index+1
        self.last_update_time=time.monotonic()
        self._deadline=self.last_update_time+self.config["interval_seconds"]

    def on_play(self):
        self.playing=True
        if self.error:
            self.playing=False
            return
        if self.controller is None:
            if self._prepare_task is None:
                self._prepare_task=asyncio.ensure_future(self._prepare())
                self._prepare_task.add_done_callback(self._prepared)
        else:
            self._deadline=time.monotonic()+self.config["interval_seconds"]

    def _prepared(self, task):
        if task.cancelled(): return
        if task.exception():
            import carb
            self.error=str(task.exception())
            self.playing=False
            carb.log_error(f"[CP-DT] 숫자 표시 초기화 실패: {self.error}")

    def on_pause(self):
        self.playing=False

    def on_stop(self):
        self.playing=False
        self._next_index=0
        if self.controller is not None: self._apply(0)

    def on_update(self, current_time, delta_time):
        if self.playing and self.controller is not None and time.monotonic()>=self._deadline:
            try:
                self._apply(self._next_index)
            except IndexError:
                self.playing=False

    def on_destroy(self):
        self.playing=False
        if self._prepare_task is not None and not self._prepare_task.done():
            self._prepare_task.cancel()
        self.controller=None
