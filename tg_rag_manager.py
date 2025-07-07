from rag.rag import get_rag_gpt_awnser


class Tg_rag_manager:
    def __init__(self, person=None, question=None):
        self._person = person
        self._question = question
        
    @property #getter
    def person(self):
        return self._person
    
    @person.setter #setter
    def person(self, person):
        if person not in ['phys', 'jurid']:
            raise ValueError("person should be 'phys' or 'jurid'") 
        self._person = person
        
    @property #getter
    def question(self):
        return self._question
    
    @question.setter #setter
    def question(self, question):
        if not isinstance(question, str):
            raise ValueError("question should be in str-like format") 
        self._question = question
        
    def get_awnser(self):
        if not isinstance(self.person, str):
            raise ValueError("person type was not stated") 
        
        if not isinstance(self.question, str):
            raise ValueError("question was not stated") 
        
        return get_rag_gpt_awnser(self.person, self.question)
        

if __name__=='__main__':
    
    tg_rag_mgr = Tg_rag_manager()
    print(f'tg_rag_mgr after init:')
    print(f'{tg_rag_mgr.person=}')
    print(f'{tg_rag_mgr.question=} \n')
    
    tg_rag_mgr.person = 'phys' # 'phys', 'jurid'
    tg_rag_mgr.question = 'Hellow world!' 
    print(f'tg_rag_mgr after assignment:')
    print(f'{tg_rag_mgr.person=}')
    print(f'{tg_rag_mgr.question=} \n')
    
    print(f'RAG+GPT awnser:')
    print(f'{tg_rag_mgr.get_awnser()}')