
from contextlib import suppress

class Notes:
    "Notes are stored in `Slides` class for consistensy."
    def __init__(self,_insatanceSlides, _instanceWidgets):
        "Instance should be inside `Slides` class."
        # print(f'Inside: {self.__class__.__name__}')
        self.main = _insatanceSlides
        self.widgets = _instanceWidgets
        self.notes_check = self.widgets.checks.notes
        self.notes_check.observe(self.__open_close_notes, names=['value'])
        
    def insert(self, content):
        """Add notes to current slide. Content could be any object except javascript and interactive widgets.
        ::: note-tip     
            In markdown, you can use alert`notes\`notes content\``."""
        if self.main.running is None:
            raise RuntimeError('Notes can only be added inside a slide constructor.')
        
        with suppress(BaseException): # Would work on next run, may not first
            self.main.running._notes = self.main.format_html(content)._repr_html_()
    __call__ = insert # Can be called as function
    
    def display(self):
        def set_value(content):
            bg = self.main.settings.colors.get('primary_bg','white')
            fg = self.main.settings.colors.get('primary_fg','black')
            bg2 = self.main.settings.colors.get('secondary_bg','#181818')
            return f"""<style>
        :root {{
            --primary-bg : {bg};
            --primary-fg : {fg};
            --secondary-bg: {bg2};
        }}
        .columns {{columns: 2 auto;}}
        .columns > div > * {{background: {bg2};padding:0.2em;font-size:120%;border-left: 2px inset {bg};}}
        .columns > div:first-child::before {{content:'This Slide';}}
        .columns > div:last-child::before {{content:'Next Slide';}}
        </style>{content}"""

        this_notes = self.main.current.notes 
        next_slide_index = (self.main.current.index + 1) % len(self.main)
        if next_slide_index > 0: # Don't loop notes back
            next_notes = self.main[next_slide_index].notes
        else:
            next_notes = ''

        notes = self.main.cols(this_notes,next_notes)
        self.widgets.notes.value = set_value(notes) 
    
    def __open_close_notes(self,change):
        if change['new'] == True:
            self.widgets.notes.popup = True
            self.display()
        else:
            self.widgets.notes.popup = False
