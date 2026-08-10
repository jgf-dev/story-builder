import vertexai

client = vertexai.Client(project="storage-499607", location="global")

# If you don't have an Agent Engine instance already, create an instance.
# agent_engine = client.agent_engines.create()

for agent in client.agent_engines.list():
    print(agent)

# projects/317234678753/locations/global/reasoningEngines/8434441657599918080

# Print the agent engine ID, you will need it in the later steps to initialize
# the ADK `VertexAiSessionService`.
# print(agent_engine.api_resource.name.split("/")[-1])
