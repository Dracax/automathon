# Exceptions module
from __future__ import (
    annotations,
)

from automathon.errors.errors import (
    InputError,
    SigmaError,
)
from collections import (
    deque,
)
from dataclasses import (
    dataclass,
)
from graphviz import (
    Digraph,
)


@dataclass
class DFA:
    """A class used to represent a Deterministic Finite Automaton (DFA).

    Attributes
    ----------
    q : set[str]
        Set of strings where each string represents a state.
        Example: q = {'q0', 'q1', 'q2'}

    sigma : set[str]
        Set of strings that represents the alphabet.
        Example: sigma = {'0', '1'}

    delta : dict[str, dict[str, str]]
        Dictionary that represents the transition function.
        Example: delta = {
                      'q0' : {'0' : 'q0', '1' : 'q1'},
                      'q1' : {'0' : 'q2', '1' : 'q0'},
                      'q2' : {'0' : 'q1', '1' : 'q2'},
                    }

    initial_state : str
        String that represents the initial state from where any input is
        processed (initial_state ∈ q / initial_state in q).
        Example: initial_state = 'q0'

    f : set[str]
        Set of strings that represent the final state/states of Q (f ⊆ Q).
        Example: f = {'q0'}

    Methods
    -------
    is_valid() -> bool
        Returns True if the DFA is a valid automata.

    accept(S : str) -> bool
        Returns True if the given string S is accepted by the DFA.

    complement() -> DFA
        Returns the complement of the DFA.

    get_nfa() -> NFA
        Converts the actual DFA to NFA and returns its conversion.

    product(m: DFA) -> DFA
        Given a DFA m, returns the product automaton.

    union(m: DFA) -> DFA
        Given a DFA m, returns the union automaton.

    view(
        file_name : str, node_attr : dict[str, str] | None, edge_attr : dict[str, str] | None
    ) -> None
        Using the graphviz library, it creates a visual representation of the DFA
        and saves it as a .png file with the name file_name"""

    q: set[str]
    sigma: set[str]
    delta: dict[str, dict[str, str]]
    initial_state: str
    f: set[str]

    def accept(self, string: str) -> bool:
        """Returns True if the given string is accepted by the DFA

        The string will be accepted if ∀a · a ∈ string ⇒ a ∈ sigma, which means
        that all the characters in string must be in sigma
        (must be in the alphabet).

        Parameters
        - - - - - - - - - - - - - - - - - -
        S : str
          A string that the DFA will try to process.
        """

        # Basic Idea: Search through states (delta) in the DFA, since the initial state to the final states

        ans = False  # Flag

        if string == "":
            ans = True
        else:
            q = (
                deque()
            )  # queue -> states from i to last character in S | (index, state)
            q.append([0, self.initial_state])  # Starts from 0

            while q and not ans:
                idx, state = q.popleft()

                if idx == len(string) and state in self.f:
                    ans = True
                elif idx < len(string):
                    if string[idx] not in self.sigma:
                        raise InputError(string[idx], "Is not declared in sigma")

                    if state in self.delta:
                        # Search through states
                        for transition in self.delta[state].items():
                            # transition: ('1', 'q0')
                            if string[idx] == transition[0]:
                                q.append([idx + 1, transition[1]])

        return ans

    def is_valid(self) -> bool:
        """Returns True if the DFA is a valid automata"""
        sigma_error_msg_not_q = "Is not declared in Q"
        sigma_error_msg_not_sigma = "Is not declared in sigma"

        # Validate if the initial state is in the set Q
        if self.initial_state not in self.q:
            raise SigmaError(self.initial_state, sigma_error_msg_not_q)

        # Validate if the delta transitions are in the set Q
        for d in self.delta:
            if d not in self.q:
                raise SigmaError(d, sigma_error_msg_not_q)

            # Validate if the d transitions are valid
            for s in self.delta[d]:
                if s not in self.sigma:
                    raise SigmaError(s, sigma_error_msg_not_sigma)
                elif self.delta[d][s] not in self.q:
                    raise SigmaError(self.delta[d][s], sigma_error_msg_not_q)

        # Validate if the final state are in Q
        for f in self.f:
            if f not in self.q:
                raise SigmaError(f, sigma_error_msg_not_q)

        # None of the above cases failed then this DFA is valid
        return True

    def complement(self) -> "DFA":
        """Returns the complement of the DFA."""
        q = self.q
        sigma = self.sigma
        delta = self.delta
        initial_state = self.initial_state
        f = {state for state in self.q if state not in self.f}

        return DFA(q, sigma, delta, initial_state, f)

    def get_nfa(self):
        from automathon.finiteAutomata.nfa import NFA

        """Convert the actual DFA to NFA class and return it's conversion"""
        q = self.q.copy()
        delta = dict()
        initial_state = self.initial_state
        f = self.f.copy()
        sigma = self.sigma

        for state, transition in self.delta.items():
            # state : str, transition : dict(sigma, Q)
            tmp = dict()
            for s, _q in transition.items():
                # s : sigma
                tmp[s] = ["".join(_q)]

            delta[state] = tmp

        return NFA(q, sigma, delta, initial_state, f)

    def product(self, m: "DFA") -> "DFA":
        """Given a DFA m returns the product automaton"""
        delta = dict()
        q = set()
        f = set()
        sigma = self.sigma.intersection(m.sigma)

        for state, transition in self.delta.items():
            # i : str, j : dict(sigma, Q)
            for state_m, transition_m in m.delta.items():
                # stateM : str, transitionM : dict(sigma, Q)
                for s in transition:
                    if s in transition_m:
                        # sigma value in common
                        sigma.add(s)

                        tmp = str([state, state_m])
                        tmp1 = str([transition[s], transition_m[s]])
                        aux = dict()
                        aux[s] = tmp1

                        q.add(tmp)
                        q.add(tmp1)

                        if state in self.f and state_m in m.f:
                            f.add(tmp)

                        if transition[s] in self.f and transition_m[s] in m.f:
                            f.add(tmp1)

                        if tmp in delta:
                            delta[tmp].update(aux)
                        else:
                            delta[tmp] = aux

        return DFA(q, sigma, delta, str([self.initial_state, m.initial_state]), f)

    def union(self, m: "DFA") -> "DFA":
        """Given a DFA  returns the union automaton"""
        tmp_nfa = self.get_nfa()
        tmp_nfa = tmp_nfa.union(m.get_nfa()).remove_epsilon_transitions()

        return tmp_nfa.get_dfa()

    def view(
        self,
        file_name: str,
        node_attr: dict[str, str] | None = None,
        edge_attr: dict[str, str] | None = None,
    ) -> None:
        dot = Digraph(
            name=file_name, format="png", node_attr=node_attr, edge_attr=edge_attr
        )

        dot.graph_attr["rankdir"] = "LR"

        dot.node("", "", shape="plaintext")

        for f in self.f:
            dot.node(f, f, shape="doublecircle")

        for q in self.q:
            if q not in self.f:
                dot.node(q, q, shape="circle")

        dot.edge("", self.initial_state, label="")

        for q in self.delta:
            for s in self.delta[q]:
                dot.edge(q, self.delta[q][s], label=s)

        dot.render()
