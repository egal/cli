class ComposeFilesSorter:

    def sort(self, files):
        def condition(element):
            return *[
                element.count("/"),
                element.count("#"),
                element.count("@"),
                element.count("/") + element.count("."),
            ], element

        files.sort(key=condition)
