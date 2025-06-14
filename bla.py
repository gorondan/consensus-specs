class Bla:
    # this is state.balances[validator_index]
    validator_balance = 32

    delegators_quotas = [0,0,0,0]
    delegated_balances = [0,0,0,0]

    delegated_validator_quota = 1
    total_delegated_balance = 0

    def apply_delegation(self, delegator_index, amount):
        self.total_delegated_balance += amount
        self.delegated_balances[delegator_index] += amount
        pass

    def recalculate_quota(self):
        if self.total_delegated_balance == 0:
            self.delegated_validator_quota = 1
            self.delegators_quotas = [0,0,0,0]
        else :
            self.delegated_validator_quota = (self.validator_balance /  (self.total_delegated_balance + self.validator_balance))
            for index in range(len(self.delegators_quotas)):
                self.delegators_quotas[index] = self.delegated_balances[index] / self.total_delegated_balance * (1-self.delegated_validator_quota)

    def apply_reward(self, amount):
        # in protocol
        validator_reward = self.delegated_validator_quota * amount

        # in protocol
        self.validator_balance += validator_reward

        # in BCA
        delegators_reward = amount - validator_reward

        # in BCA
        for index in range(len(self.delegators_quotas)):
            self.delegated_balances[index] += delegators_reward * self.delegators_quotas[index]
        pass


    def report(self):
        print('validator_balance ', self.validator_balance)
        print('delegators_quotas ', self.delegators_quotas)
        print('delegated_balances ', self.delegated_balances)
        print('delegated_validator_quota ', self.delegated_validator_quota)
        print('total_delegated_balance ', self.total_delegated_balance)
        print('------ ')

    def test_quota_1(self):
        sum = 0
        sum += self.delegated_validator_quota

        for index in range(len(self.delegators_quotas)):
            sum += self.delegators_quotas[index]

        print("Total quota in DV", sum)

bla = Bla()
bla.report()

bla.apply_delegation(1, 2)
bla.apply_delegation(2, 2)
bla.recalculate_quota()
bla.report()

bla.apply_reward(10)


bla.report()

bla.test_quota_1()

