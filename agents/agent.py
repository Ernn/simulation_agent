import random
from utils.text_generation import generate, get_rating
import networkx as nx

class Agent:

    """
    A class to represent an individual agent in a simulation similar to The Sims.

    Attributes:
    -----------
    name : str
        The name of the agent.
    description : str
        A brief description of the agent.
    location : str
        The current location of the agent in the simulated environment.
    memories : list
        A list of memories the agent has about their interactions.
    compressed_memories : list
        A list of compressed memories that summarize the agent's experiences.
    plans : str
        The agent's daily plans, generated at the beginning of each day.

    Methods:
    --------
    plan(global_time, town_people, prompt_meta):
        Generates the agent's daily plan.
    
    execute_action(other_agents, location, global_time, town_areas, prompt_meta):
        Executes the agent's action based on their current situation and interactions with other agents.
    
    update_memories(other_agents, global_time, action_results):
        Updates the agent's memories based on their interactions with other agents.
    
    compress_memories(memory_ratings, global_time, MEMORY_LIMIT=10):
        Compresses the agent's memories to a more manageable and relevant set.
    
    rate_locations(locations, town_areas, global_time, prompt_meta):
        Rates different locations in the simulated environment based on the agent's preferences and experiences.
    """

    def __init__(self, name, description, starting_location, world_graph, use_openai):
        self.name = name
        # self.age = age
        # self.innate_traits = innate_traits
        self.description = description
        self.location = starting_location
        self.memory_ratings = []
        self.memories = []
        self.compressed_memories = []
        self.plans = ""
        self.last_plan = ""
        self.world_graph = world_graph
        self.use_openai = use_openai

        ### wyb
        self.conversation = []
        ###
        
        ### lqh
        self.reted_memories = []
        self.importance_index = 0
        self.importance_score = 0
        self.reflect_thres = 100
        ###

    ### creation:lqh todo:lyh
    def rate_memory(self,memory):
      """
        Rates the agent's memories based on their importance.
      """
      return 1
    
    ### creation:lqh todo:lyh   
    def retrieve(self,memo_num = 10,quiry=""):
      """
        retrieve #memo_num relevant memories to the query based on their recency, importance, and relevance .
      """
      return ['[Time: {}. Person: {}. Memory: {}. Importance_score: {}.]']
        
    ### creation:lqh
    def update_rated_memories(self, other_agents, global_time, action_results):
        
        """
        Updates the agent's memories based on their interactions with other agents.
        
        Parameters:
        -----------
        other_agents : list
            A list of other Agent objects in the simulation.
        global_time : int
            The current time in the simulation.
        action_results : dict
            A dictionary of the results of each agent's action.
        importance_score: int
            A score indicating the importance of the results of each memory.
        """

        for agent in other_agents:
            if agent.location == self.location:
                memory = action_results[agent.name]
                importance_memory = self.rate_memory(memory)
                self.importance_score += importance_memory
                self.memories.append('[Time: {}. Person: {}. Memory: {}. Importance_score: {}.]\n'.format(str(global_time), agent.name, memory, importance_memory))
                if self.importance_score>self.reflect_thres:
                  self.generate_reflections
                    
    ### creation:lqh 
    def generate_reflections(self,num_quiries=3,num_memories=10,prompt_meta=""):
      self.importance_score = 0
      # generate quiries
      prompt = ""
      for (i,memory) in enumerate(self.rated_memories[self.importance_index:]):
        prompt.append("{}. {}; ".format(str(i), self.rated_memories.split('Memory:')[1])).split('.')[0]
      prompt.append("Given only the information above, what are {} most salient high-level questions we can answer about the subjects in the statements?".format(str(num_quiries)))
      quiries = generate(prompt_meta.format(prompt))
      quiries = quiries.split('?') # quiries转化为列表

      for quiry in quiries:
        prompt = ""
        # retrieve relevant memories
        relevant_memories = self.retrieve(memory,num_memories)  ######

        #generate insights
        # name
        names = {}
        for (i,memory) in enumerate(relevant_memories):
          prompt.append("{}. {}; ".format(str(i), memory.split('Memory:')[1].split('.')[0]))
          person = memory.split('.')[1].split(':')[1]
          if person in names.keys():
            names[person]+=1
          else:
            names[person] =1
        person = max(names, key=lambda x: names[x])
        prompt = "Statements about {}:".format(person)
        prompt.append("Given only the information above, What {} high-level insights can you infer from the above statements? (example format: insight(because of 1, 5, 3))".format(str(num)))
        insight = generate(prompt_meta.format(prompt))

        #parse and store time
        self.update_rated_memories(self, [person], global_time, {person:insight}) ####
      self.importance_index = len(self.rated_memories)
      return None
    

    def __repr__(self):
        return f"Agent({self.name}, {self.description}, {self.location})"

    def plan(self, global_time, prompt_meta):
        """
        Generates the agent's daily plan.
        
        Parameters:
        -----------
        global_time : int
            The current time in the simulation.
        prompt_meta : str
            The prompt used to generate the plan.
        """

        prompt = "You are {}. The following is your description: {} You just woke up. What is your goal for today? Write it down in an hourly basis, starting at {}:00. Write only one or two very short sentences. Be very brief. Use at most 50 words.".format(self.name, self.description, str(global_time))
        # prompt =   "You are {}, and you are {} years old. Your innate traits are {}. The following is your description: {}\n
        # On {}, You {}.\n
        # Today is {}. Here is your plan today in broad strokes: 1)".format(self.name, self.age, self.innate_traits, self.description, global_last_date, self.last_plan, global_date)
        self.plans = generate(prompt_meta.format(prompt), self.use_openai)

    def execute_action(self, other_agents, location, global_time, town_areas, prompt_meta):

        """Executes the agent's action based on their current situation and interactions with other agents.
        
        Parameters:
        -----------
        other_agents : list
            A list of other Agent objects in the simulation.
        location : Location
            The current Location object where the agent is located.
        global_time : int
            The current time in the simulation.
        town_areas : dict
            A dictionary of Location objects representing different areas in the simulated environment.
        prompt_meta : str
            The prompt used to generate the action.

        Returns:
        --------
        action : str
            The action executed by the agent.
        """

        people = [agent.name for agent in other_agents if agent.location == location]

        prompt = "You are {}. Your plans are: {}. You are currently in {} with the following description: {}. It is currently {}:00. The following people are in this area: {}. You can interact with them.".format(self.name, self.plans, location.name, town_areas[location.name], str(global_time), ', '.join(people))

        people_description = [f"{agent.name}: {agent.description}" for agent in other_agents if agent.location == location.name]
        prompt += ' You know the following about people: ' + '. '.join(people_description)

        prompt += "What do you do in the next hour? Use at most 10 words to explain."
        action = generate(prompt_meta.format(prompt), self.use_openai)

        # whether talk with somebody
        prompt = "You are {}. Next you are going to: {}. Does it mean you want to have a conversation with someone? If not, just answer 'No'. If so, who do you want to talk to? Just answer its name.".format(self.name, action)
        whether_talk = generate(prompt_meta.format(prompt), self.use_openai)
        if whether_talk != 'No':
            agent2_name = whether_talk
            self.have_a_talk(action, agent2_name, other_agents, global_time, prompt_meta)
            action += '\n' + '\n'.join(self.conversation)
            self.conversation = []    # refresh
        return action

    def update_memories(self, other_agents, global_time, action_results):

        """
        Updates the agent's memories based on their interactions with other agents.
        
        Parameters:
        -----------
        other_agents : list
            A list of other Agent objects in the simulation.
        global_time : int
            The current time in the simulation.
        action_results : dict
            A dictionary of the results of each agent's action.
        """

        for agent in other_agents:
            if agent.location == self.location:
                self.memories.append('[Time: {}. Person: {}. Memory: {}]\n'.format(str(global_time), agent.name, action_results[agent.name]))

    def compress_memories(self, global_time, MEMORY_LIMIT=10):

        """
        Compresses the agent's memories to a more manageable and relevant set.
        
        Parameters:
        -----------
        global_time : int
            The current time in the simulation.
        MEMORY_LIMIT : int, optional
            The maximum number of memories to compress. Default is 10.

        Returns:
        --------
        memory_string : str
            The compressed memory string.
        """

        memories_sorted = sorted(self.memory_ratings, key=lambda x: x[1], reverse=True)
        relevant_memories = memories_sorted[:MEMORY_LIMIT]
        memory_string_to_compress = '.'.join([a[0] for a in relevant_memories])
        return '[Recollection at Time {}:00: {}]'.format(str(global_time), memory_string_to_compress)

    def rate_memories(self, locations, global_time, prompt_meta):

        """
         Rates the agent's memories based on their relevance and importance.
        
        Parameters:
        -----------
        locations : Locations
            The Locations object representing different areas in the simulated environment.
        global_time : int
            The current time in the simulation.
        prompt_meta : str
            The prompt used to rate the memories.

        Returns:
        --------
        memory_ratings : list
            A list of tuples representing the memory, its rating, and the generated response.
        """

        memory_ratings = []
        for memory in self.memories:
            prompt = "You are {}. Your plans are: {}. You are currently in {}. It is currently {}:00. You observe the following: {}. Give a rating, between 1 and 5, to how much you care about this.".format(self.name, self.plans, locations.get_location(self.location), str(global_time), memory)
            res = generate(prompt_meta.format(prompt), self.use_openai)
            rating = get_rating(res)
            max_attempts = 2
            current_attempt = 0
            while rating is None and current_attempt < max_attempts:
                rating = get_rating(res)
                current_attempt += 1
            if rating is None:
                rating = 0
            memory_ratings.append((memory, rating, res))
        self.memory_ratings = memory_ratings
        return memory_ratings


    def rate_locations(self, locations, global_time, prompt_meta):

        """
        Rates different locations in the simulated environment based on the agent's preferences and experiences.
        
        Parameters:
        -----------
        locations : Locations
            The Locations object representing different areas in the simulated environment.
        global_time : int
            The current time in the simulation.
        prompt_meta : str
            The prompt used to rate the locations.

        Returns:
        --------
        place_ratings : list
            A list of tuples representing the location, its rating, and the generated response.

        """

        place_ratings = []
        for location in locations.locations.values():
            prompt = "You are {}. Your plans are: {}. It is currently {}:00. You are currently at {}. How likely are you to go to {} next?".format(self.name, self.plans, str(global_time), locations.get_location(self.location), location.name)
            res = generate(prompt_meta.format(prompt), self.use_openai)
            rating = get_rating(res)
            max_attempts = 2
            current_attempt = 0
            while rating is None and current_attempt < max_attempts:
                rating = get_rating(res)
                current_attempt += 1
            if rating is None:
                rating = 0
            place_ratings.append((location.name, rating, res))
        self.place_ratings = place_ratings
        return sorted(place_ratings, key=lambda x: x[1], reverse=True)

    def move(self, new_location_name):

        if new_location_name == self.location:
            return self.location

        try:
            path = nx.shortest_path(self.world_graph, source=self.location, target=new_location_name)
            self.location = new_location_name
        except nx.NetworkXNoPath:
            print(f"No path found between {self.location} and {new_location_name}")
            return self.location

        return self.location

    def have_a_talk(self, action, agent2, other_agents, global_time, prompt_meta):
        for another_agent in other_agents:
            if agent2 == another_agent.name:
                self.conversation.append('[Conversation between {} and {}]'.format(self.name, agent2))
                prompt = "You are {}. Your plans are: {}. It is currently {}:00. And you are going to {}. ".format(self.name, self.plans, global_time, action)
                prompt += " You know the following about {}: {}".format(another_agent.name, another_agent.describtion)
                prompt += " What would you say to {}?".format(another_agent.name)
                sentence = generate(prompt_meta.format(prompt), self.use_openai)
                self.conversation.append("{}: {}".format(self.name, sentence))

                trigger = True
                turn = 0
                while trigger:
                    if turn == 0:
                        person_1 = another_agent
                        person_2 = self
                    else:
                        person_1 = self
                        person_2 = another_agent
                    prompt = "You are {}. Your plans are: {}. It is currently {}:00. Now {} is talking to you.".format(person_1.name, person_1.plans, global_time, person_2.name)
                    prompt += " You know the following about {}: {}\n".format(person_2.name, person_2.describtion)
                    prompt += 'Here is the dialogue history:\n' + '\n'.join(self.conversation)
                    prompt += " \n How would you respond to {}? If you decide to end the conversation, just answer 'End'.".format(person_2.name)
                    sentence = generate(prompt_meta.format(prompt), self.use_openai)
                    if sentence != 'End':
                        self.conversation.append("{}: {}".format(self.name, sentence))
                    else:
                        trigger = False
