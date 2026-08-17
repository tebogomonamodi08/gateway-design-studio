'''
Gateway v1:
upload->parse->validate->store->notify
'''

from nicegui import ui
from pprint import pprint #for inspection, pretty print
import yaml
from model import GatewayConfig
from pydantic import ValidationError

def handle_upload(e):
    
    config_container.clear()
    advisor_container.clear()
    error_container.clear()
    content = e.file._data #check for a better API to access the bytes of this object
    '''###############Debugger#############'''
    pprint(content)
    '''##############################'''
    ui.notify('Successfully uploaded.', color='green')
    config = yaml.safe_load(content) 
    pprint(config) 
    
    try:
        gateway_config = GatewayConfig.model_validate(config)
        ui.notify('File validated', color='green')
        with config_container:
            print('Reached config container')
            with ui.card().classes('p-5 border border-blue-400 rounded-xl bg-slate-900'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Deployment Configuration').classes('text-2xl font-bold text-white text-left')
                    ui.badge('Validated').props('color=green')
                deployment = gateway_config.model_list[0]
                with ui.column().classes('items-left justify-between w-full gap-4'):
                    ui.label(f'Deployment Name: {deployment.model_name}')
                    ui.label(f'Model: {deployment.litellm_params.model}')
    
                
    except ValidationError:
        gateway_config=None
        ui.notify('Error validating the configuration', color='red')
        with error_container:
            with ui.card().classes('p-5 border border-blue-400 rounded-xl bg-slate-900'):
                ui.label('Error')
                
    
    return gateway_config


    
    
    
with ui.column().classes('w-full items-center'):
    with ui.card().classes( 'w-full max-w-4xl mx-auto p-6 rounded-xl border border-blue-400 bg-slate-900'):
        ui.label('Gateway design Studio').classes('text-2xl font-bold text-white')
        ui.label('Configuration Management & Observability').classes('text-gray-400')
        with ui.card().classes('items-center w-full max-w-4xl mx-auto p-8 rounded-xl border-2 border-dashed border-blue-400 bg-slate-900'):
            ui.icon('upload').classes('text-5xl text-blue-400 items-center')
            ui.label('Upload config.yaml').classes('text-2xl font-bold text-white')
            ui.label('Drag and drop or click to browse').classes('text-gray-400')
            ui.upload(on_upload=handle_upload).classes('px-8 py-3 rounded-xl text-lg font-semibold '
             'bg-blue-500 hover:bg-blue-400 text-white '
             'shadow-lg shadow-blue-500/40 '
             'hover:scale-105 transition-all duration-300 '
             'animate-pulse').props('color=primary unelevated').props("label='Choose File' color=primary flat")
            
            # Placeholders live here
            config_container = ui.column().classes('w-full max-w-4xl')
            advisor_container = ui.column().classes('w-full max-w-4xl')
            error_container = ui.column().classes('w-full max-w-4xl')
    

ui.run(dark=True)
