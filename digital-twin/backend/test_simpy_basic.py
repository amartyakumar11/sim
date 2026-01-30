"""Test basic SimPy functionality"""
import simpy

def rider_process(env, name, resource):
    print(f"{name}: Arriving at {env.now}")
    req = resource.request()
    print(f"{name}: Waiting for resource")
    yield req
    print(f"{name}: Got resource at {env.now}")
    yield env.timeout(2)
    print(f"{name}: Done at {env.now}")
    resource.release(req)

env = simpy.Environment()
resource = simpy.Resource(env, capacity=1)

env.process(rider_process(env, "R1", resource))
env.process(rider_process(env, "R2", resource))

env.run(until=10)
print("Simulation complete")
