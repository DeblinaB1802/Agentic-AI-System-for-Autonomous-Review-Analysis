import pickle
from tqdm import tqdm
from analyzer.sentiment import SentimentAnalyzerAgent
from analyzer.summary import ReviewOverviewAgent
from analyzer.issues import IssueDetectorAgent
from analyzer.usp import USPDectectorAgent
from analyzer.trend import TrendAnalyzerAgent
from memory_manager import ProductMemory
from context_builder import build_context
from Utils.helpers import autonomous_task_selection

class MultiAgent:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self.AgentMemory = {} 
        self.SentimentAnalyzerAgent = SentimentAnalyzerAgent(self.model)
        self.ReviewOverviewAgent = ReviewOverviewAgent(self.model)
        self.IssueDetectorAgent = IssueDetectorAgent(self.model)
        self.USPDectectorAgent = USPDectectorAgent(self.model)
        self.TrendAnalyzerAgent = TrendAnalyzerAgent(self.model)

    def create_product_memory_and_prioritize_tasks(self, data):
        tasks_assigned, quality_parameter = autonomous_task_selection(data)
        product_name = data['product_name'].iloc[0]
        product_memory = ProductMemory(product_name)
        if tasks_assigned == []:
            return product_memory, tasks_assigned, quality_parameter

        for i, row in tqdm(data.iterrows(), total=len(data), desc="Processing Reviews"):
            row = dict(row)
            context = build_context(row, product_memory)
            result = self.SentimentAnalyzerAgent.adaptive_sentiment_analysis(row['customer_review'], context)
            result = self.SentimentAnalyzerAgent.estimate_weightage(result)
            product_memory.update(result, context)
            self.AgentMemory[product_name] = product_memory

        return product_memory, tasks_assigned, quality_parameter
    
    def save_product_memory(self, product_name, product_memory):
        memo_path = rf"C:\Users\debli\OneDrive\Desktop\CV_PROJECT\AGENTIC_AI_BASED_REVIEW_ANALYZER\data\memory\{product_name}.pkl"
        with open(memo_path, "wb") as f:
            pickle.dump(product_memory, f)







