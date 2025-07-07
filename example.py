from tg_rag_manager import Tg_rag_manager

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