#create a 


class Pronoun: 
    def __init__(self, subjective, objective, possesive_weak, posessive_strong, reflexive, gramatically_plural = False):
        self.subjective = subjective
        self.objective = objective
        self.posessive_weak = possesive_weak 
        self.posessive_strong = posessive_strong
        self.reflexive = reflexive 
        self.gramatically_plural = gramatically_plural
        
    def equivalent_pronoun(self, pronoun_case):
        case_pronoun_switch = {
            'SUBJ' : self.subjective, 
            'OBJ' : self.objective,
            'POSS_WK' : self.posessive_weak,
            'POSS_STRG' : self.posessive_strong,
            'REFLX' : self.reflexive
        }
        return case_pronoun_switch.get(pronoun_case)

