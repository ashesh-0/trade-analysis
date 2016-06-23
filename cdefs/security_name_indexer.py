## @brief Singleton class to map/convert a security's shortcode and exchange symbol to an id and vice versa.
#  Once we have mapped the symbol to an id, we can work just with id's for all securities, and get
#  the symbols using this class whenever required
#
class SecurityNameIndexer():

    unique_instance = None  # Unique instance of this singleton class

    def __init__(self):
        self.secname_dict = {}
        self.secname_list = []
        self.shortcode_list = []
        self.tradable_shortcode_list = []

    ## @brief Static function to get a reference to the unique instance of this class
    @staticmethod
    def GetUniqueInstance():
        if SecurityNameIndexer.unique_instance is None:
            SecurityNameIndexer.unique_instance = SecurityNameIndexer()
        return SecurityNameIndexer.unique_instance

    ## @brief Static function to delete the unique instance of this class, if it exists
    @staticmethod
    def RemoveUniqueInstance():
        if SecurityNameIndexer.unique_instance is not None:
            SecurityNameIndexer.unique_instance = None
        return SecurityNameIndexer.unique_instance

    def add_symbol(self, shortcode):
        self.secname_list.append(None)
        self.shortcode_list.append(shortcode)
        self.tradable_shortcode_list.append(shortcode)

    def get_shortcode_from_id(self, id):
        if id >= len(self.shortcode_list):
            return None
        return self.shortcode_list[id]
