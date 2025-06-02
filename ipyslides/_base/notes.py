
class Notes:
    "Notes are stored in `Slides` class for consistensy."
    def __init__(self,_insatanceSlides, _instanceWidgets):
        "Instance should be inside `Slides` class."
        self.main = _insatanceSlides
        self.widgets = _instanceWidgets
        self.notes_check = self.widgets.checks.notes
        self.notes_check.observe(self.__open_close_notes, names=['value'])
        
    def insert(self, content):
        r"""Add notes to current slide. Content could be any object except javascript and interactive widgets.
        ::: note-tip     
            In markdown, you can use alert`notes\`notes content\``."""
        self.main.verify_running('Notes can only be added inside a slide constructor.')
        self.main.this._notes = self.main.html('',[content]).value

    __call__ = insert # Can be called as function
    
    def display(self):
        def set_value(content):
            colors, _colors = self.main.settings._colors, {}
            if self.widgets.theme.value == 'Jupyter': # Try to match inherit theme
                _colors = self.widgets.iw._colors
            bg  = _colors.get('bg1',colors.get('bg1','white'))
            fg  = _colors.get('fg1',colors.get('fg1','black'))
            bg2 = _colors.get('bg2',colors.get('bg2','#181818'))
            font = self.main.settings.fonts.props.get('text', 'Roboto')
            return f"""<style>
        :root {{
            --bg1-color : {bg};
            --fg1-color : {fg};
            --bg2-color: {bg2};
        }}
        .columns {{columns: 2 auto;font-family: {font};}}
        .columns > div > * {{background: {bg2};padding:4px;border-left: 2px inset {bg};margin-block:0 !important;}}
        .columns > div:first-child::before {{content:'This Slide';font-size:80%;font-weight:bold;}}
        .columns > div:last-child::before {{content:'Next Slide';font-size:80%;font-weight:bold;}}
        </style>{content}"""

        this_notes = self.main._current.notes 
        next_slide_index = (self.main.wprogress.value + 1) % len(self.main) 
        if next_slide_index > 0: # Don't loop notes back
            next_notes = self.main[next_slide_index].notes
        else:
            next_notes = ''

        notes = self.main.cols(this_notes,next_notes)
        self.widgets.notes.value = set_value(notes) 
    
    def _popup_display(self):
        self.widgets.notes.popup = True
        self.display()
    
    def __open_close_notes(self,change):
        if change['new'] == True:
            self.main.widgets.iw._try_exec_with_fallback(self._popup_display)
        else:
            self.widgets.notes.popup = False
