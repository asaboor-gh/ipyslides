import sys
import dashlab 

from contextlib import contextmanager
from .formatters import get_slides_instance

@contextmanager
def _hold_running_slide_builder():
    "Hold the running slide builder to restrict slides specific content inside general dashbaorads."
    if (slides := get_slides_instance()):
        with slides._hold_running():
            yield
        slides.run_animation(selector=dashlab.base._this_klass) # automatically run animation after this content
    else:
        yield

dashlab.base._user_ctx = _hold_running_slide_builder # patch dashlab to hold running slide builder # type: ignore
sys.modules[__name__] = dashlab # re-export dashlab