from langgraph.store.memory import InMemoryStore
import uuid
import os
import keyring

# Initialize the memory state
in_memory_store = InMemoryStore()

# Define a user namesapce(user_id + "memories")
user_id = "1"
namesapce_for_memory = (user_id, "memories")

# Store a memory (food preference)
memory_id = str(uuid.uuid4())
memory = {"food_preference":"I like pizza"}
in_memory_store.put(namesapce_for_memory, memory_id, memory)

# Retrieve the stored memories
memories = in_memory_store.search(namesapce_for_memory)

print(memories[-1].dict())      # {"value": {"food_preference":"I like pizza"}, ...}