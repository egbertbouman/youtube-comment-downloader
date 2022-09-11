import json

class Comment:
    def __init__(self,dict) -> None:
        self.dict = dict

    def __repr__(self) -> str:
        return (json.dumps(self.dict,indent=4))
        
    def __getitem__(self,indice) -> str:
        return self.dict[indice]

