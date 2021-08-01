title_page = '''
__slides_mode = False #Set this to True and run all cells below
#Fixed Parameters Initialization
__slides_dict = {} #Don't edit
__dynamicslides_dict = {} #Don't edit

from IPython.display import display, Markdown

# Do NOT change variable name, just edit value
title_page_md=""" # Interactive Slides  
<em> Author: Abdul Saboor</em>

- %%capture \_\_slide_[N] on cell top auto picks slide
- List or tuple assigned to \_\_next_to_[N] generates slides dynamically
- Edit `%%html` cell for theme

> Restart Kernel if you make mistake in slide numbers to avoid hidden state problem.

> For JupyterLab >=3, do `pip install sidecar`
"""
'''
