'''
Gateway v1:
upload->parse->validate->store->notify
'''


from nicegui import ui
from pprint import pprint #for inspection, pretty print
import yaml
from model import GatewayConfig
from pydantic import ValidationError


ui.add_head_html(
    '<script src="https://unpkg.com/cytoscape/dist/cytoscape.min.js"></script>'
)

##########Application state############

class GatewayState:
    def __init__(self):
        self.config  = None
        self.topology = None
        
    def build_topology(self):
        nodes = []
        if self.config:
            nodes = [{'id':'Gateway', 'name':'Gateway','type':'gateway'}]
            edges = []
            for model in self.config.model_list:
                nodes.append({
                    'id': model.model_name,
                    'name': model.litellm_params.model,
                    'type': 'deployment'
                })
                edges.append({'Gateway':model.litellm_params.model})
            self.topology = { 'nodes': nodes,
                             'edges':edges
                 }
                
                
    
                
app_state = GatewayState()

def render_topology():
    '''This function will render the topology of the configuration using the gateway's 
    topology'''





def handle_upload(e):
    
    config_container.clear()
    advisor_container.clear()
    error_container.clear()
    preview_container.clear()
    content = e.file._data.decode('utf-8') #check for a better API to access the bytes of this object
    '''###############Debugger#############'''
    #pprint(content)
    '''##############################'''
    ui.notify('Successfully uploaded.', color='green')
    config = yaml.safe_load(content) 
    #pprint(config) 
    
    with preview_container.classes('w-full max-w-4xl items-center'):
        with preview_container:
            with ui.card().classes('w-full p-5 rounded-xl border border-blue-400 bg-slate-900'):
                ui.label('Configuration Preview').classes('text-xl font-bold text-white')

                with ui.column().classes('w-full p-3 rounded-lg bg-[#0B1220] gap-1'):
                    for i, line in enumerate(content.splitlines(), start=1):
                        with ui.row().classes('w-full gap-3'):
                            ui.label(str(i)).classes('text-gray-500 font-mono w-6')
                            ui.label(line).classes('text-white font-mono')
    
    try:
        gateway_config = GatewayConfig.model_validate(config)
        app_state.config = gateway_config
        
        #####Discovery#############
        print(f'This is the object {gateway_config}')
        for model in gateway_config.model_list:
            print(f'Model  ID: {model.model_name}')
            print(f'model: {model.litellm_params.model}')
        
        
        
        
        
        ############################
        ui.notify('File validated', color='green')
        with config_container.classes('w-full max-w-4xl items-center'):
            print('Reached config container')
            with ui.card().classes('w-full p-5 border border-blue-400 rounded-xl bg-slate-900'):
                with ui.row().classes('w-full justify-between items-center'):
                    ui.label('Deployment Configuration').classes('text-2xl font-bold text-white text-left')
                    ui.badge('Validated').props('color=blue')
                deployment = gateway_config.model_list[0]
                with ui.column().classes('w-full gap-4 p-5 rounded-xl bg-slate-800 border border-blue-500'):
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('Model Name:')
                        ui.label(f'{deployment.model_name}').classes('text-lg font-semibold text-white')
                        
                    with ui.row().classes('w-full justify-between items-center'):
                        ui.label('Deployment')
                        ui.label(deployment.litellm_params.model).classes('text-lg font-semibold text-white')
                        
    
                
    except ValidationError as err:
        if not content.strip():
            ui.notify('No content in the uploaded file', color='yellow')
        else:
            ui.notify('Error validating the configuration', color='red')
            with error_container:
                with ui.card().classes('w-full p-3 rounded-lg bg-slate-800 border border-red-500'):
                     with ui.row().classes('w-full justify-between items-center'):
                        ui.label('Configuration Diagnostics').classes('text-xl font-bold text-red-400')
                        ui.badge('Validation Failed').props('color=red')
                     ui.separator()
                for error in err.errors():
                    field = " → ".join(str(x) for x in error["loc"])

                    with ui.card().classes('w-full p-3 rounded-lg bg-slate-800 border border-red-500'):
                        ui.label(field).classes('text-red-300 font-semibold')
                        ui.label(error["msg"]).classes('text-gray-300')
                
    
    return gateway_config
        
#####Discovery###########



    
    
    
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
            preview_container = ui.column().classes('w-full max-w-4xl')
            config_container = ui.column().classes('w-full max-w-4xl')
            
            advisor_container = ui.column().classes('w-full max-w-4xl')
            error_container = ui.column().classes('w-full max-w-4xl')
            
            
            
            topology_container = ui.html('<div id="topology" style="width:100%; height:600px;">Tebogo</div>').classes("w-full")
            
            
    

ui.run(dark=True)
