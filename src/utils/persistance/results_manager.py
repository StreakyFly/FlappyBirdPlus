from .file_manager import FileManager


class ResultsManager(FileManager):
    def __init__(self, results_file="results.json"):
        super().__init__()
        self.results_file = results_file
        self.default_results = {
            "results": [],
        }
        self._initialize_results()
        self.results = self._load_results()

    def _initialize_results(self):
        """ Initialize results if they do not exist. """
        if not self.file_exists(self.results_file):
            self.save_results(self.default_results)

    def _load_results(self):
        """ Load results from the results file. """
        return self.load_file(self.results_file, default=self.default_results)['results']

    def save_results(self, results):
        """ Save results to the results file. """
        self.save_file(self.results_file, results)

    def reset_results(self):
        """ Reset results to default. """
        self.save_results(self.default_results)
        return self.default_results

    def add_result(self, score: int, timestamp: str):
        """ Add a result to the results. """
        self.results['results'].append({'score': score, 'timestamp': timestamp})
        self.save_results(self.results)
