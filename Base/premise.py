from App.models import Premise


class PremiseInstance:
    real_verified = Premise.get_premise_by_name('realVerified', None).body
    # assert real_verified
