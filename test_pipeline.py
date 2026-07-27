"""Quick test — Open window with deferred + IBL pipeline, no model needed."""
import logging
import sys
import os

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
_log = logging.getLogger("test_window")

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


def main():
    from render.app import RendererApp

    app = RendererApp(
        model_path="",
        window_title="Karin DX11 - Pipeline Test",
        width=960,
        height=720,
    )

    _log.info("=" * 50)
    _log.info("Pipeline Status:")
    _log.info("  Deferred: %s", app._deferred._enabled if app._deferred else False)
    _log.info("  IBL loaded: %s", app._ibl_loader.is_loaded() if hasattr(app, '_ibl_loader') else False)
    _log.info("  PostProcess: %s", app._postprocess._enabled if app._postprocess else False)
    _log.info("  Cascade shadows: %s",
              app._deferred._cascade_shadow is not None if app._deferred else False)
    _log.info("=" * 50)
    _log.info("Press ESC or close window to exit")
    _log.info("=" * 50)

    try:
        app.run()
    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
