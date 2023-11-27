# TODO: Remove all TODO comments once the implementation is complete.
"""
TODO: Add the Paper Title on this line.
TODO: Add the paper's PDF URL (preferably from arXiv) on this line.

TODO: Write a Short Description of the task.

Homepage: TODO: Add the URL to the task's Homepage here.
"""
import json
import os
import tarfile
import requests
from urllib.request import urlopen
from lm_eval.base import rf, MultipleChoiceTask


# TODO: Add the BibTeX citation for the task.
_CITATION = """
"""

# sample doc 
#{"id": "88efefe1-7726-11ea-9116-54bef70b159e", "question": {"stem": "A Terra é um planeta telúrico, pois", "choices": [{"text": "apresenta crusta silicatada", "label": "A"}, {"text": "é um planeta de reduzidas dimensões", "label": "B"}, {"text": "é interior à cintura de asteroides", "label": "C"}, {"text": "apresenta baixa densidade", "label": "D"}]}, "answerKey": "A", "info": {"grade": 12, "subject": "Biology", "language": "Portuguese"}}

def generate_all_exams_loglikelikelihoods_tasks():
    languages=["pt", "es", "fr", "gm", "vm"]
    return {
        f"exams_{language}": globals()[f"EXAMS_{language.upper()}"] for language in languages
    }


# TODO: Replace `NewTask` with the name of your Task.
class EXAMS(MultipleChoiceTask):
    VERSION = 0
    # TODO: Add the `DATASET_PATH` string. This will be the name of the `Task`
    # dataset as denoted in HuggingFace `datasets`.
    DATASET_PATH = "data/exams"
    # TODO: Add the `DATASET_NAME` string. This is the name of a subset within
    # `DATASET_PATH`. If there aren't specific subsets you need, leave this as `None`.
    DATASET_NAME = "EXAMS"

    language="Portuguese"

    def __init__(self, data_dir=None, cache_dir=None, download_mode=None):
        
        self.download(data_dir, cache_dir, download_mode)
        self._training_docs = None
        self._fewshot_docs = None

    def download(self, data_dir=None, cache_dir=None, download_mode=None):
        # download the dataset from url
        url="https://github.com/mhardalov/exams-qa/raw/main/data/exams/multilingual/test.jsonl.tar.gz"
        if not os.path.exists(self.DATASET_PATH):
            os.makedirs(self.DATASET_PATH, exist_ok=True)
            response = requests.get(url)
            file_path = os.path.join(self.DATASET_PATH, 'test_exams.tar.gz')

            # Save the file
            with open(file_path, 'wb') as file:
                file.write(response.content)

            # Extract the file
            with tarfile.open(file_path, 'r:gz') as tar:
                tar.extractall(path=self.DATASET_PATH)

        task_data={
            "test": []
        }

        with open(os.path.join(self.DATASET_PATH, "test.jsonl"), "r") as f:
            for line in f:
                task_data["test"].append(json.loads(line))

        
        # filter test data to only include language
        task_data["test"] = list(filter(lambda x: x["info"]["language"] == self.language, task_data["test"]))

        self.dataset = task_data

    def has_training_docs(self):
        return False

    def has_validation_docs(self):
        return False

    def has_test_docs(self):
        return True

    def test_docs(self):
        if self.has_test_docs():
            
            return map(self._process_doc, self.dataset["test"])

    def _process_doc(self, doc):

        query=doc["question"]["stem"]
        choices=[]
        for choice in doc["question"]["choices"]:
            choices.append(f"{choice['text']}")
        gold=doc["answerKey"]

        # map gold to integer, A-0, B-1, C-2, D-3
        gold = ord(gold) - 65

        return {
            "query": query,  # The query prompt.
            "choices": choices,  # The list of choices.
            "gold": gold,  # The integer used to index into the correct element of `"choices"`.
        }

    def doc_to_text(self, doc):
        return doc["query"]


class EXAMS_GREEDY(EXAMS):

    def doc_to_text(self, doc):

        alternatives = doc["choices"]
        
        return doc["query"] + "\n" + "\n".join(alternatives) + "\n" + "ANSWER:"
    
    def doc_to_target(self, doc):
        return " " + ['A.', 'B.', 'C.', 'D.', 'E.'][doc['gold']]

    def construct_requests(self, doc, ctx):
        """ Uses RequestFactory to construct Requests and returns an iterable of 
        Requests which will be sent to the LM.

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param ctx: str
            The context string, generated by fewshot_context. This includes the natural 
            language description, as well as the few shot examples, and the question
            part of the document for `doc`. 
        """
        print("ctx",ctx)
        print("doc",doc)
        continuation = rf.greedy_until(ctx, {
            "until": "\n"
        })
        return continuation

    def _process_doc(self, doc):

        query=doc["question"]["stem"]
        choices=[]
        for choice in doc["question"]["choices"]:
            choices.append(f"{choice['label']}: {choice['text']}")
        gold=doc["answerKey"]

        # map gold to integer, A-0, B-1, C-2, D-3
        gold = ord(gold) - 65

        return {
            "query": query,  # The query prompt.
            "choices": choices,  # The list of choices.
            "gold": gold,  # The integer used to index into the correct element of `"choices"`.
        }

    def process_results(self, doc, results):
        """Take a single document and the LM results and evaluates, returning a
        dict where keys are the names of submetrics and values are the values of
        the metric for that one document

        :param doc:
            The document as returned from training_docs, validation_docs, or test_docs.
        :param results:
            The results of the requests created in construct_requests.
        """
        gold = ['A.', 'B.', 'C.', 'D.', 'E.'][doc['gold']]

        
        pred = results[0]
        
        print("pred",pred)

        acc = 1. if pred == gold else 0.

        return {
            "acc": acc,
            "acc_norm": acc,
        }


class EXAMS_FR(EXAMS):
    language="French"

class EXAMS_ES(EXAMS):
    language="Spanish"

class EXAMS_PT(EXAMS):
    language="Portuguese"

class EXAMS_GM(EXAMS):
    language="German"

class EXAMS_VM(EXAMS):
    language="Vietnamese"