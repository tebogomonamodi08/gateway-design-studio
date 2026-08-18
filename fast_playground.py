from nicegui import ui

def handle():
    ui.run_javascript('alert("Press")')

ui.button('Press', on_click=handle)

ui.run(dark=True)

