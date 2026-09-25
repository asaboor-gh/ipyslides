from ..formatters import slidebound
from ..xmd import xmd, _internal_xmd_call


class Notes:
    r"""Add notes to current slide. Content could be any object except javascript and interactive widgets.
    
    Note that notes are not shown inside slides during presentation. They can be viewed in popup window by 
    enabling `Notes Popup` option in settings panel. Notes can also be printed in PDF (after export too) by 
    enabling `Inline Notes` option in settings panel, useful for sharing slides with notes or for personal reference.
    
    ::: note.tip     
        - In markdown, you can use [alert! [notes\! notes content \/] /].
        - Place your (extended) projector on top/bottom of laptop screen while presenting 
          in Jupyter Notebook to allow right/left edges click navigation work smoothly.
    """
    def __init__(self,_insatanceSlides, _instanceWidgets):
        "See class docstring for usage."
        self.main = _insatanceSlides
        self.widgets = _instanceWidgets
        self.notes_check = self.widgets.checks.notes
        self.notes_check.observe(self.__open_close_notes, names=['value'])
    
    @_internal_xmd_call('notes', True) # register notes for xmd usage, will be overwritten by instance later   
    @slidebound("notes")
    def __call__(self, content):
        "See class docstring for usage."
        if not isinstance(content, str): raise TypeError("Notes content must be a string.")
        self.main.this._notes = xmd(content, True, "div") # p tag takes extra space, using div for notes
    
    def display(self):
        def set_value(content):
            colors, _colors = self.main.settings._colors, {}
            if self.widgets.theme.value == 'Jupyter': # Try to match inherit theme
                _colors = self.widgets.iw._colors
            fg  = _colors.get('fg1',colors.get('fg1','black'))
            bg2 = _colors.get('bg2',colors.get('bg2','#181818'))
            bg = f'hsl(from {bg2} h s calc(l*1.5))' # avoid bg1 if user set slides background as gradient
            font = self.main.settings.fonts.props.get('text', 'Roboto')
            return f"""<style>
        :root {{
            --bg1-color : {bg};
            --fg1-color : {fg};
            --bg2-color: {bg2};
        }}
        body {{margin: 0;padding: 4px;overflow: hidden;}}
        .popup-notes {{font-family: {font};background: {bg};color: {fg};height: 100%;}}
        .popup-notes > div {{background: {bg2};padding:4px;border-radius: 0.25em;margin-block:0 !important;max-height: 100%;overflow: auto;}}
        .popup-notes > div:last-child {{overflow: hidden; height: calc(100% - 8px);}}
        .next-notes {{font-size: 0.8em;}}
        ::-webkit-scrollbar {{width: 3px;height: 3px;}}
        ::-webkit-scrollbar-corner {{display: none;}}
        *:hover::-webkit-scrollbar {{background: #8988;}}
        *:hover::-webkit-scrollbar-thumb {{background: #898f;}}
        </style>{content}"""

        this_notes = self.main._current.notes 
        next_slide_index = (self.main.wprogress.value + 1) % len(self.main) 
        if next_slide_index > 0: # Don't loop notes back
            next_notes = self.main[next_slide_index].notes
        else:
            next_notes = ''
        
        next_notes = self.main.html('div', f'''
            <div style="display:flex;justify-content:space-between;align-items:center;padding-bottom:0.25em;flex-wrap:wrap;white-space:pre;">
                <span id="countup" style="font-weight:bold;">⏱️ 00:00</span>
                <span>🕑<b id='timer'>Time</b></span>
            </div>
            <h2 style="font-size:0.5em;opacity:0.5;border-bottom: 1px solid #8988;">Next Slide Notes</h2>
            <div class="next-notes" style="max-height: 100%; overflow-y: auto;overflow-x: hidden;">
            {next_notes}
            </div>''', style= {'height': '100%', 'display': 'grid', 'grid-template-rows': 'auto auto 1fr'}
        )
        
        notes = self.main.stack([this_notes,next_notes], sizes=[3,2], css_class='popup-notes')
        self.widgets.notes.value = set_value(notes) 
    
    def _popup_display(self):
        self.widgets.notes.popup = True
        self.display()
    
    def __open_close_notes(self,change):
        if change['new'] == True:
            self.main.widgets.iw._try_exec_with_fallback(self._popup_display)
        else:
            self.widgets.notes.popup = False
