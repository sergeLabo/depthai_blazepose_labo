


from oscpy.server import OSCThreadServer


osc = OSCThreadServer()
sock = osc.listen(address='127.0.0.1', port=8000, default=True)

@osc.address(b'/action')
def callback(*values):
    print(f"actions: {values}")

@osc.address(b'/depth')
def callback(*values):
    print(f"depth: {values}")

osc.stop()
