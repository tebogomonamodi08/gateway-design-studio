'''
Gateway v1:
upload->parse->validate->store->notify
'''

from nicegui import ui
from pprint import pprint #for inspection, pretty print
import yaml

def handle_upload(e):
    content = e.file._data #check for a better API to access the bytes of this object
    '''###############Debugger#############'''
    pprint(content)
    '''##############################'''
    ui.notify(f'{e.file.name} successfully uploaded.', color='green')
    print(yaml.safe_load(content))
    return yaml.safe_load(content)  
    
    
    
    
    

ui.upload(on_upload=handle_upload)

ui.run(dark=True)
