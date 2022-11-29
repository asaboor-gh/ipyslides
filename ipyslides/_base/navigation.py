"""
Author Notes: Classes in this module should only be instantiated in LiveSlide class or it's parent class
and then provided to other classes via composition, not inheritance.
"""

class Navigation:
    def __init__(self, _instanceWidgets):
        "Instnace should be inside `LiveSlide` class."
        # print(f'Inside: {self.__class__.__name__}')
        self.widgets = _instanceWidgets
        self.progress_slider = self.widgets.sliders.progress
        self.btn_next = self.widgets.buttons.next
        self.btn_prev = self.widgets.buttons.prev
        self.btn_settings = self.widgets.buttons.setting
        self.visible_slider = self.widgets.sliders.visible
    
        
        self.btn_prev.on_click(self.__shift_left)
        self.btn_next.on_click(self.__shift_right)
        self.btn_settings.on_click(self.__toggle_panel)
        self.visible_slider.observe(self.__set_hidden_height,names=['value'])
        
    def __shift_right(self,change):
        self.widgets.slidebox.remove_class('Prev') # remove backwards animation safely
        if change:
            try:
                self.progress_slider.index = self.progress_slider.index + 1 # Forwards
            except:
                self.progress_slider.index = 0 # loop back to title page at end of presentation
            
            self.__change_icon(self.progress_slider.index)
            
    def __shift_left(self,change):
        self.widgets.slidebox.remove_class('Prev') # remove backwards animation safely
        if change:
            self.widgets.slidebox.add_class('Prev') # Backwards Animation
            if self.progress_slider.index == 0:
                self.progress_slider.index = len(self.progress_slider.options) - 1 # loop back to last slide
            else:
                self.progress_slider.index = self.progress_slider.index - 1 # Backwards
            
            self.__change_icon(self.progress_slider.index)
    
    def __change_icon(self, current_index):
        if '.' in self.progress_slider.options[current_index - 1][0]:
            self.btn_prev.icon = 'chevron-up'
        else:
            self.btn_prev.icon = 'chevron-left'
        
        next_idx = (current_index + 1) % len(self.progress_slider.options)
        if '.' in self.progress_slider.options[next_idx][0]:
            self.btn_next.icon = 'chevron-down'
        else:
            self.btn_next.icon = 'chevron-right'
    
    def __toggle_panel(self,change):
        if self.btn_settings.description == '\u2630':
            self.btn_settings.description  = '⨉'
            self.widgets.panelbox.layout.display = 'flex'
            self.btn_next.disabled = True
            self.btn_prev.disabled = True
        else:
            self.btn_settings.description = '\u2630'
            self.widgets.panelbox.layout.display = 'none'
            self.btn_next.disabled = False
            self.btn_prev.disabled = False
            
    def __set_hidden_height(self,change):
        self.widgets.slidebox.layout.height = f'{self.visible_slider.value}%'
        self.widgets.slidebox.layout.margin='auto 4px'
        
        