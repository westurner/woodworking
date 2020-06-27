#!/usr/bin/env python3
import math
from fractions import Fraction
from typing import List
#from typeshed.numbers import Number
from numbers import Number

from tabulate import tabulate
#import pint
#ureg = pint.UnitRegistry()

from sympy import Rational


class Conf:
    FORMAT_CONTEXT = False  # Whether to apply format_context to Bench._repr_html_


def format_context(ctx):
    return Context({x: express_in(y) for (x,y) in ctx.items()})


class List(list):
    def __str__(self):
        return "List%s" % (list.__str__(self))


def express_in(number: Number, tostr=True):
    _floor = math.floor(number)
    _remaining = Rational(number-_floor)
    if _floor == 0:
        _remaining = Rational(_remaining)
        if tostr:
            return '%s"' % _remaining
        else:
            return Rational(_remaining)
    if tostr:
        if _remaining:
            return '%s-%s"' % (_floor, _remaining)
        else:
            return '%s"' % (_floor)
    else:
        return (_floor, _remaining)


def test_express_in():
    assert express_in(Rational("7/2"), tostr=False) == (3, Rational("1/2"))
    assert express_in(0.5625, tostr=False) == Rational("9/16")


class Lumber2x:
    standard_lengths = [96, 144, 192]


class Lumber2x4(Lumber2x):
    height = 1.5 # * ureg.inches
    width = 3.5 # * ureg.inches


class TreatedLumber2x4(Lumber2x):
    height = Rational("3/2")  # + Rational("1/8")) # * ureg.inch  # 1 1/2
    width = (Rational("7/2") + Rational("1/8"))  # * ureg.inch  # 3 5/8


class TreatedLumber4x4(Lumber2x):
    height = width = (Rational("7/2") + Rational("1/8"))  # * ureg.inch  # 3 5/8


class Lumber2x6(Lumber2x):
    height = 1.5 # * ureg.inches
    width = 5.5 # * ureg.inches
    
    # standard_lengths = [8*12, 12*12, 16*12]
    


class Context(dict):
    def set(self, key, value):
        self[key] = value
        print((key, value))
        
    def _repr_html_(self):
        return tabulate(self.items(), tablefmt='html')


####


import itertools

class Cutlist:
    def __init__(self, available): # =Lumber2x6.standard_lengths):
        """
        Arguments:
            available (list): list of available lengths
        """
        self.cx = Context()
        self.cx['available'] = available

    @staticmethod
    def iter_combinations(items: List):
        for n in reversed(range(1, len(items)+1)):
            for combo in itertools.combinations(items, n):
                yield sorted(combo, reverse=True)
        
    def findsolutions(self, needed: List, extralength: Number=1):
        """
        calculate a cutlist
        
        Arguments:
            neededlengths (list): list of lengths needed
        Keyword Arguments:
            extralength (Number): extra length to require
                to account for variance in actual lengths and cut widths (default=1)
        """
        available = sorted(self.cx['available'], reverse=True)
        needed = sorted(needed, reverse=True)
        combinations = list(self.iter_combinations(needed))
        
        possible_combinations = []
        for combo in combinations:
            length = sum(combo)
            for avail in available:
                if (length + extralength) < avail:
                    possible_combinations.append(
                        {'boardlength': avail,
                         'possiblecuts': combo,
                         'overage': avail-sum(combo)
                        })
        sorted_possible_combinations = sorted(
            possible_combinations,
            
            # Do we want to:
            # - buy the longest possible boards (likely* the cheapest)
            # - minimize overage
            # - make sure it fits in the truck bed (or through the sunroof)
            #key=lambda x: (x['overage'], -1*x['boardlength'])
            key=lambda x: (-1*x['boardlength'], x['overage'])
        )
        boards = []
        
        def do_the_rest():
            for combo in sorted_possible_combinations:
                if not len(needed):
                    break
                _cuts = []
                for length in combo['possiblecuts']:
                    try:
                        needed.remove(length)
                        _cuts.append(length)
                    except ValueError:
                        continue  # TODO: this is waste because the rest of the board is unused
                if _cuts:
                    combo['cuts'] = _cuts
                    combo['cutsoverage'] = combo['boardlength'] - sum(_cuts)
                    boards.append(combo)
            return boards
        def do_the_rest2():
            i = 0
            print(('needed', needed))
            while needed:
                possiblecombo = sorted_possible_combinations[i]
                i += 1
                for neededcombo in self.iter_combinations(needed):
                    if neededcombo == possiblecombo['possiblecuts']:
                        for length in neededcombo:
                            if length not in needed:
                                continue
                            else:
                                needed.remove(length)
                                print((length, needed))
                        combo = possiblecombo.copy()
                        combo['cuts'] = neededcombo
                        combo['cutsoverage'] = combo['boardlength'] - sum(neededcombo)
                        boards.append(combo)
            return boards
        def do_the_rest3():
            i = 0
            print(('needed', needed))
            while needed:
                possiblecombo = sorted_possible_combinations[i]
                i += 1
                for neededcombo in self.iter_combinations(needed):
                    if neededcombo == possiblecombo['possiblecuts']:
                        for length in neededcombo:
                            if length not in needed:
                                continue
                            else:
                                needed.remove(length)
                                print((length, needed))
                        combo = possiblecombo.copy()
                        combo['cuts'] = neededcombo
                        combo['cutsoverage'] = combo['boardlength'] - sum(neededcombo)
                        boards.append(combo)
            return boards
        #return do_the_rest()
        return do_the_rest2()

            
# rethinking the problem in pseudocode
def cutlist(needed, available):
    # objectives:
    # - buy the longest boards possible
    # - minimize waste / overage
    
    # tasks:
    # find_densest_packings
    # fulfill needed set with densest packings first
    pass
    
                    
            
def test_cutlist():
    cutlist = Cutlist(Lumber2x6.standard_lengths)
    needed = []
    [needed.extend([101.75, 58-1.5, 69]) for n in range(4)]
    
    solution = cutlist.findsolutions(needed)
    overage = 0
    for l in solution:
        print(l)
        overage += l['cutsoverage']
    print(f'board count: {len(solution)}')
    print(f'total overage: {overage}')
    raise Exception()
            

        
