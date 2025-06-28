from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.prebuilt import ToolNode, tools_condition

from tools.weather_info_tool import WeatherInfoTool
from tools.place_search_tool import PlaceSearchTool
from tools.expense_calculator_tool import CalculatorTool
from tools.currency_conversion_tool import CurrencyConverterTool
from utils.model_loader import ModelLoader
from prompt_library.prompt import SYSTEM_PROMPT

class GraphBuilder():
    def __init__(self, model_provider:str = "groq"):
        self.tools = []
        self.model_laoder = ModelLoader(model_provider = model_provider)
        self.llm = self.model_loader.load_llm()

        self.weather_tools = WeatherInfoTool()
        self.place_search_tools = PlaceSearchTool()
        self.calculator_tools = CalculatorTool()
        self.currency_converter_tools = CurrencyConverterTool()

        self.tools.extend([
            * self.weather_tools.weather_tool_list,
            * self.place_search_tools.place_search_tool_list,
            * self.calculator_tools.calculator_tool_list,
            * self.currency_converter_tools.currency_converter_tool_list
        ])

        self.graph = None
        self.system_prompt = SYSTEM_PROMPT
        self.llm_with_tools = self.llm_bind_tools(tools=self.tools)

    def agent_fucntion(self,state: MessagesState):
        "Main agent function"
        user_question = state["messages"]
        input_question = [self.system_prompt] + user_question
        response = self.llm_with_tools.invoke(input_question)
        return {"messages":[response]}
    
    def build_graph(self):
        graph_builder=StateGraph(MessagesState)
        graph_builder.add_node("agent",self.agent_fucntion)
        graph_builder.add_node("tools",ToolNode(tools=self.tools))
        graph_builder.add_edge(START,"agent")
        graph_builder.add_conditional_edges("agent",tools_condition)
        graph_builder.add_edge("tools","agent")
        graph_builder.add_edge("agent",END)

        self.graph = graph_builder.compile()
        return self.graph
    
    def __call__(self):
        return self.build_graph()