# Study and extension of the Magpie framework : notes

***

### Useful links

Documentation on Magpie's external libraries

[Pathlib Documentation](https://docs.python.org/3/library/pathlib.html)

[Runpy Documentation](https://docs.python.org/3/library/runpy.html)

## Thoughts

***
+ method(): Type
Magpie is a tool for automated software improvement 

To achieve its goal, it provides three functionalities :

 - Ways to turn a given software into an abstract **model** of itself, so we are able to modify it(to apply *edits* 
    on it) efficiently

 - **Algorithms** to look for the best combination of edits(the best *patch*) to apply to a given software

 - **Fitness Functions** to compare multiple versions(multiple *variants*) of a given software on a given criteria( 
   examples of fitness functions include : the amount of **tests** passed by the software, or it's **time complexity**)

Magpie provides the abstract representation and basic methods of those three functionalities, as well the necessary
classes to make them work( we need things like way to represent patches, software, variants, functions to
create and apply edits, etc.) in its *core* folder

Currently, all core classes are in a single folder. This is not a problem *per se,* as it does not impair functionality 
or performance or even testability, but separating data classes from functionality classes would make the project
structure clearer at first glance.

here are the inheritance structure for models and algorithms :

<img src = "./src/img/Model_inherintance_diagram.drawio.png"/>

*figure 1 : class diagram illustrating the inheritance structure for models*

<img src= "./src/img/Algorithm_class_diagram.drawio.png"/>

*figure 2 : class diagram illustrating the inheritance structure for algorithms*

Data on software evolution is structured in different object types : Edits, Patches, Variants and the software itself 
typed BasicSoftware

An edit is a modification in the software. In code, it contains a  *target*(a variant of software on which the edit 
will apply) and a list of args(I don't know ho they are used yet)

A patch is composed of a list of edits on the same software variant

A variant is a software on which a patch as been applied. It contains a BasicSoftware, a dict called *models*,
but I can't tell what that one is supposed to be, and the last attribute is a called diff, and is a LiteralString. It's
 a value expressing the difference between the variant and another variant of the same software. I would be curious
to know how this value is calculated, there seems to be multiple methods of calculation nad I guess the model used to
make edits is relevant in the calculation as well.

here is a class diagram showing the dependencies listed above

<img src="./src/img/Update_Data_Dependencies.drawio.png">

*figure 3 : class diagram for dependencies between data classes*

*We can spot a circular dependency between AbstractEdit, Patch and Variant, which might make unit testing less effective*

Project structure seems close to a visitor pattern : on one side, the data(software, variants, patches, edits), on the 
other, functionality(models of abstraction, editing algorithms, fitness functions). I will need further study to confirm
this

Taking a look at the *bin* folder now, we can see that this the classes contained are meant to parse the magpie command
arguments. As a reminder, magpie currently implements seven different processes :

 - **ablation analysis** I still don't know what this is exactly
 - processes working on produced patches : **minify** and **revalidate**
 - visualisation tools : **show_location** and **show_patch**
 - the currently implemented software evolution algorithm **local_search** and **genetic_programming**, kind of where
 the money is

Knowing which of those classes you will enter when launching magpie is the job of the **\_\_main__** folder at the root
of the project, using the first argument given after launching the magpie project which is the process you want to launch. 
The next arguments you give are the **processes arguments** : things like the path to your scenario file, the exact
evolution algorithm you want to use, the seed for rng edits, etc. It is the *bin* folder classes job to parse those
arguments, put them in a config dict, create the **Protocol** object(class described in *core/basic-protocol.py*) that will 
that will actually be in charge of running the chosen protocol.

Has an example, here is the typical execution flow for the following command :

```bash
    pyhton3 magpie local_search --scenario examples/minisat/_magpie/scenario_runtime_config1.txt
```

<img src="src/img/bin_sequence_diagram.drawio.png" />

*figure 4 : sequence diagram illustrating the typical execution flow of magpie(part 1).*

Later, we will take a closer look at the Protocol class by illustrating its execution flow using a sequence diagram 
based on the same use case (local search). This will help us visualize a typical execution sequence at the scale 
of the entire project.

Continuing with the bin folder, we can observe a significant amount of duplicated code, which suggests that refactoring 
is possible. The file pairs genetic_programming.py and local_search.py, as well as minify_patch.py and 
revalidate_patch.py, could likely be merged into single files with only minimal code changes. I will discuss this 
further in the Suggestions section. It is also likely that additional refactoring opportunities remain, as a 
considerable amount of duplicated code would still be present even after these changes.

for now, let's take a look at the project's global structure and make conjectures concerning the design pattern we would
like to apply. Here is a complete UML diagram illustrating magpie's global structure, without going into the details of 
each class's methods :

<img src="./src/img/full_class_diagram.png">

*figure 5 : Complete class diagram of magpie*

Looking at the algorithm module, we can see a use of the **template method pattern**. It is visible both in the class
diagram, that shows a heavy use of inheritance in this module, and in the code itself. Let's recall the definition of 
the template method pattern:

*The template method pattern defines the skeleton of an algorithm in a method, deferring some steps to subclasses.
Template Method lets subclasses redefine certain steps of an algorithm without changing the algorithm's structure.*(source 2)

and see how it applies to our code base. Here, the template method is the `run` method defined in the AbstractAlgorithm
class:

```python
 @abc.abstractmethod
    def run(self):
        pass
```

As we can see, this method does not actually provide any structure. That is because the search algorithm themselves who directly
extends the BasicAlgorithm class(here LocalSearch and GeneticProgramming) will be providing that structure and defer some
steps to their subclasses.

The `AbstractAlgorithm` class is here to provide hook methods and other useful methods that all search algorithm are going to
need, as well as to make the implementation of the `run` method mandatory for all subclasses. Hook methods are an integral
part of the template method pattern. They are *methods declared in the abstract class, but only given an empty or 
default implementation*, allowing subclasses to override them or not. A problem of the current codebase is that the
hook methods are **not** implemented in the abstract class but in the `BasicAlgorithm` class, wich implements the abstract
class but does not provide an implementation of the `run` method, as no search algorithm object should be instantiated 
as `BasicAlgorithm`, which means it should be an abstract class. This is both confusing and bug inducing, as right now
`BasicAlgorithm` object can be instantiated, but will do nothing in a normal execution flow because they do not implement
`run`.

Now Let's see how the classes that inherit from AbstractAlgorithm and BasicAlgorithm apply the template pattern with 
the example of local search, which is the simplest of the two. The template method, run, describes the general structure : 

```python
class LocalSearch(magpie.core.BasicAlgorithm):

    def run(self):
        try:
            # warmup
            self.hook_warmup()
            self.warmup()

            # early stop if something went wrong during warmup
            if self.report['stop']:
                return

            # start!
            self.hook_start()

            # main loop
            current_patch = self.report['best_patch']
            current_fitness = self.report['best_fitness']
            while not self.stopping_condition():
                self.hook_main_loop()
                current_patch, current_fitness = self.explore(current_patch, current_fitness)

        except KeyboardInterrupt:
            self.report['stop'] = 'keyboard interrupt'

        finally:
            # the end
            self.hook_end()

    @abc.abstractmethod
    def explore(self, current_patch, current_fitness):
        pass

    def mutate(self, patch):
        n = len(patch.edits)
        if n == 0:
            if self.config['delete_prob'] == 1:
                self.report['stop'] = 'trapped'
            else:
                patch.edits.append(self.create_edit(self.software.noop_variant))
        elif random.random() < self.config['delete_prob']:
            del patch.edits[random.randrange(0, n)]
        else:
            patch.edits.append(self.create_edit(self.software.noop_variant))
```

The steps are as follows :

 - warmup
 - check for stopping condition
 - if false, execute main loop( here simply execute `self.explore()`)
 - if true, return

*this global structure is similar in genetic_programming, but the main loop is far more complex and there is more calculation
before going into it*

As we can see, the explore behavior is the one left to be defined by the subclasses. The mutate behavior will be used in 
several of those, which uis why it is defined in the abstract class. Because local search( and genetic programming) algorithms
have a lot of variant that use the same structure with only one changing behavior, the use of the template method pattern
is a great choice for their implementation.

In a proper use of the template method pattern, the classes that LocalSearch and GeneticProgramming inherit from, AbstractAlgorithm
and BasicAlgorithm should provide the overarching structure for a search algorithm, and the run method should just be the part of it
that is left for the subclasses to implement, like explore() in LocalSearch and crossover() for GeneticProgramming but, 
as we saw above, that is not the case, as the abstract run() method of AbstractAlgorithm is not used anywhere in it or in 
Basic Algorithm. That ends up making those names kind of misleading, as the classes they refer to  have little to do 
with the search algorithms themselves, and much more to do with evaluation and logging of patches and software
variants. As such their work is much more one of a planer, executing each step of the software improvement protocol(warmup,
error checking, logging, evaluation of variants) than it is of an algorithm, and I think fusing them in a single class
and naming it protocol would be much better suited, but of course it would mean the hook methods in there would stop 
making sense(they already don't, but we'll get to that in a bit).

Hook methods are supposed to provide additional "optional" behaviors for the template algorithm, for which the template
class provides a default or empty implementation, letting the subclasses the freedom of overriding them or not, changing
those behavior or adding new on top. Here, that is not what those methods actually are. First of all, hook methods 
should be called **by the template class that implements them** and not the subclasses. The subclasses can just choose 
they *override* the method or not, not whether the method is *called*. Hook methods are *always* called, as they are 
considered part of the template algorithm, but here *there is no template algorithm*, only hook methods that are not really
hooks(most of them don't even help the algorithm function) and helper method that are *used* by the algorithms.

Now to be fair, there is some logic in those two classes that is essential to the algorithm functioning properly, and
there is already a Protocol class in the project. But I just feel like the content of those two classes should be distributed
between a proper algorithm class and the already present Protocol class, instead of being in two separate and misleadingly 
named classes that do not gain anything from being separated. Right now, the component that monitors the algorithm
IS the algorithm, instead of HAVING the algorithm it is supposed to monitor as an attribute. This makes the search algorithms more tedious
to test and the overall execution flow less flexible.

A better approach would be to decouple the control logic(software evaluation pipeline, logging, error checking) from the 
specific search behaviors(local search and genetic programming), while different algorithms could define their behavior 
independently of evaluation, logging, or lifecycle orchestration. This would allow testing them independently of those
superfluous steps and thus more accurately. It also would allow more flexibility in execution plans and protocol.
As shown by the sequences diagram up above, the user currently is limited to using a single algorithm per execution cycle. 
With more loosely coupled components, we could imagine for example running any genetic programming
algorithm and then running minify on the best resulting patch, and even looping over those two steps multiple times
all in a single execution cycle, but as of right now it's not possible.

*The strategy pattern defines a family of algorithm, encapsulates each one, and makes them interchangeable. Strategy lets 
the algorithm vary independently of clients that use it*(source 2)

Here is an example of what an actual template method pattern would look like for this project:

```python
#implementation of the search algorithms of magpie based on the template method pattern.
class SearchAlgorithm:    
    #template of the algorithm
    def run(self):
        self.hook_start()
        while not self.stopping_condition():
            self.hook_main_loop()
            self.main_loop()
        self.hook_end()

    #if we need extra calculation before the main loop
    def hook_start(self):
        pass

    #if wee need extra calculation at each step
    def hook_main_loop(self):
        pass

    #main loop of search algo, to be implemented by subclasses
    @abc.abstractmethod
    def main_loop(self):
        pass

    #if we need extra calculation at the end of the algorithm
    def hook_end(self):
        pass
    
    #else, returns false
    def stopping_condition(self):
        return False
```

*example simplified for clarity's sake. complete example is available at /magpie/algos/template/template_search_algorithm.py*

The existing `Protocol` class could take over lifecycle control entirely — including warmup, logging, and evaluation. 
Search algorithms would simply be passed in as pluggable strategies, allowing the protocol to operate on them like any 
other tool. This would cleanly separate control logic from algorithm logic.

## Suggestions 

***

Here I will report places where I think the code can be improved and make suggestions for improvements.

### Deleting duplicate class in *model* folder

currently, each model folder contains an abstract representation of said model. Two of those representation, however, 
**are exactly the same classes**, minus their name, as we can see on fig 1. The BasicModel class is also not very useful
and could probably be discarded, if we move the setup method in the AbstractModel class. here is the new structure I 
suggest :

<img src="./src/img/new_model_structure.png"/>

The setup method has been moved up and particular classes for each abstract models have been replaced with a general 
one : AbstractRIDModel(for Abstract Replace Insert Delete Model) that the classes for concrete models can implement. We
thus get rid of duplicate classes and make the structure clearer.

I also noticed that the astor model implements the RID model but does not inherit it. With this structure, no need to
create a new abstract class, we can just make the class inherit the AbstractRIDModel class. That is also true of all
future classes implementing this model.

### Refactoring in the *bin* folder

The bin folder files are in charge of parsing the arguments of the protocol chosen by the user and build the 
corresponding Protocol object. Currently, the folder is structured as follows :

```
magpie
├── algos
├── bin
│   ├── __init__.py
│   ├── ablation_analysis.py
│   ├── genetic_programming.py
│   ├── local_search.py
│   ├── minify_patch.py
│   ├── revalidate_patch.py
│   ├── show_locations
│   └── show_patch
├── core
.
.
.
├──__main__.py
.
.
```

When looking at the code, we notice a lot of redundancy. The genetic_programming.py and local_search.py are almost the 
same, having only a few lines of difference, and the same goes for minify_patch.py and revalidate_patch.py. In both of 
those cases we could easily merge them in a single file each, with only minimal code change in the newly created files
and the \_\_main__.py root file. Here is the new structure I suggest :

```
magpie
├── algos
├── bin
│   ├── __init__.py
│   ├── software_improvement.py
│   ├── patch_operations.py
│   └── visualizer.py
├── core
.
.
.
├──__main__.py (updated)
.
.
```

Here I also combined the show_location.py and show_patch.py into the visualizer.py file This refactor would trim down 
the code considerably, going from 7 to 3 files while keeping the file size mostly the same and getting rid of a lot
of duplicate code. Furthermore, this change would make the structure clearer by putting the different protocols into
three distinct categories : the automatic software improvement protocols, the protocols making operations on patches,
and the visualization protocols.


### Separating responsibilities in the BasicAlorithm class

*Single responsibility* is one of the basic rules for good design in software engineering. The single responsibility
of the BasicAlgorithm class should be to provide the operations necessary to run a search algorithm, but by looking at
the code, I noticed that it does a lot more than that.

The setup method for example, is part of the `BasicAlgorithm` object's build process, and could easily be done by the
`Protocol` object calling a function in the setup.py file.

The *hook* methods in that class are pretty confusing. When starting my study I thought those where supposed to run the
search algorithm, turns out they are just logging, checking for errors and printing the report datas. I suggest moving them into their own
separate class and document it to make their purpose more clear, and the `BasicAlgorithm` code easier to understand.

<img src="src/img/hook_class.drawio.png"/>

The main problem with this refactor is that some of the currently implemented search algorithm override the hook methods present in `BasicSoftware`. A simple solution to this, however, is to create an inner class that would inherit the basic `Hook` class(we could even rename it `BasicHook`), and give the search algorithm an object of this class instead. As an example, here is what the code of `ValidSearch` would look like :

```python
class ValidSearch(LocalSearch):

   class ValidSearchHook(BasicHook):

      def __init__():
         super.init()

      def hook_warmup(self, algo):
         super().hook_warmup()
         if algo.debug_patch is None:
               raise RuntimeError

      def hook_start(self, algo):
         super().hook_start()
         algo.report['best_fitness'] = None
         algo.report['best_patch'] = self.debug_patch

      def hook_evaluation(self, algo, variant, run, accept=False, best=False):
         # accept
         accept = best = False
         if run.status == 'SUCCESS':
               best = algo.dominates(run.fitness, algo.report['best_fitness']) or (run.fitness == algo.report['best_fitness'] and len(variant.patch.edits) < len(algo.report['best_patch'].edits))
               accept = best or run.fitness == algo.report['best_fitness']
               if best:
                  algo.report['best_fitness'] = run.fitness
                  algo.report['best_patch'] = variant.patch

         super().hook_evaluation(variant, run, accept, best)

        # next
        self.stats['steps'] += 1

    def __init__(self):
         super().__init__()
         self.debug_patch = None
         self.hook = ValidSearchHook()


    def do_cleanup(self, variant):
         cleaned = copy.deepcopy(variant)
         for k in reversed(range(len(variant.patch.edits))):
            patch = copy.deepcopy(cleaned.patch)
            del patch.edits[k]
            tmp = magpie.core.Variant(self.software, patch)
            if tmp.diff == variant.diff:
                self.software.logger.info('removed %s', cleaned.patch.edits[k])
                cleaned = tmp
         s1, s2 = len(cleaned.patch.edits), len(variant.patch.edits)
         if s1 < s2:
            self.software.logger.info('cleaned size is %d (was %d)', s1, s2)
            self.software.logger.info('clean patch: %s', cleaned.patch)
         return cleaned
```

Another challenge of this refactor is that the hook operations need access to the search algorithm's data to work. 
As you can see up here, I solved this by making the hook methods take a search algorithm as argument, 
turning the class into a **visitor-like utility**. This makes for more decoupling, but will introduce more verbose, 
as the method call in the algo will now require it to pass itself : 

```python 
#from
self.hook_wramup()

#to
self.hook.warmup(self)
```

This change will definitely make the code a bit more laborious to write, however it will make it a lot 
clearer and easier to understand.

**I made this suggestion with an incomplete understanding of hook methods and the template method pattern. Because of that
it's kinf of wobbly and not very relevant to the actual code base. For those reasons, this suggestion will not be implemented.**

### Evaluation pipelines attributes in `BasicSoftware`

The `BasicSofwtare` class is responsible for the execution of it's own evaluation pipeline

We know that the pipeline consists of five commands: `init`, `setup`, `compile`, `test` and `run`. Each of those commands have 
four attributes : 
 - `cmd` : the command itself
 - `performed` : a boolean value indicating if the command as been performed yet or not
 - `timeout` : a time limit for the command's execution
 - `lengthout` : a length limit for the command's output

Currently, the `BasicAlgorithm` class is reserving one field for each attribute, for each command, for a total of twenty
fields reserved for the evaluation pipeline. Having this much resembling fields introduces a lot of code redundancy,
most notably in the setup section of the class initialization :

```python
        if 'init_cmd' in config['software']:
            if config['software']['init_cmd'].lower() in ['', 'none']:
                self.init_cmd = None
            else:
                self.init_cmd = config['software']['init_cmd']
        if 'init_timeout' in config['software']:
            if config['software']['init_timeout'].lower() in ['', 'none']:
                self.init_timeout = None
            else:
                self.init_timeout = float(config['software']['init_timeout'])
        if 'init_lengthout' in config['software']:
            if config['software']['init_lengthout'].lower() in ['', 'none']:
                self.init_lengthout = None
            else:
                self.init_lengthout = int(config['software']['init_lengthout'])
```

This piece of code is repeated five times, with the only change being the attribute's name. There is two ways to fix 
this :

 - Having a dict field for each command

```python
#from
self.setup_performed = False
self.setup_cmd = None
self.setup_timeout = None
self.setup_lengthout = None

#to
self.setup = {
    'performed' : False,
    'cmd' : None,
    'timeout' : None,
    'lengthout' : None
}
```

 - Creating a `Command` data class

```python
class Command :

    def __init__(self): 
        self.performed = False,
        self.cmd = None,
        self.timeout = None,
        self.lengthout = None
```

In both cases, these changes would allow us to factorize the init code(and other not mentioned pieces) into a separate
method to which we would simply pass the right command attribute.

In my opinion this refactor would make the code shorter and clearer(Keep It Simple Stupid), and more scalable.
In particular, the data class option would make it a lot easier to add a new command in the pipeline.

### Misc

 - At core/abstract_model.py 75 : method update-cli does nothing. Could be removed
 - In the BasicProtocol class : a few minor changes can be made. Most importantly : the software attribute is not needed,
    as it is used only to be passed to the search attribute. Why not pass the software to the search algo as an attribute
    *before* creating the protocol with the search attribute?
 - In the `BasicAlgorithm` class, the setup method mostly just processes and copies data from its config argument and
    checks for errors in aforementioned data. This means data duplication. Instead of doing that, we could do all the 
    processing and error checking on the protocol's `config['search']` dictionary, and pass a reference to it to the 
    `BasicAlgorithm` object as an attribute. As a whole, it would be good if every part of the execution sequence read 
    and modified a single `config` dict, making copies only when strictly necessary, as useless copies induce errors
    and data duplication
 - I noticed some occurrences of dead variables in the code, most notably in the `BasicAlgorithm` class(signaled by comments). 
    Variables and dict values are assigned, then re-assigned later without being used once. These make the code 
    more confusing and induce errors.
 - having three "hook evaluation" method is probably unnecessary.I would have to look further into it to make sure, but 
   they could probably be replaced by a single method with different arguments in the call. here is what it would look 
    like:
    ```python
    def hook_evaluation(self, variant, run, accept=False, best=False, force_success=False):
    data = self.aux_log_data(variant.patch, run, self.aux_log_counter(), self.report['reference_fitness'], accept, best)
    self.aux_log_print(data, run, accept, best)
    if run.status != 'SUCCESS' and force_success:
        self.software.diagnose_error(run)
    ```
   by having all the data necessary and with the new `force_success` argument, I believe this method can replace the 
    three methods we currently have if the calls are slightly changed.


***

## Changelog

### Refactoring in the bin folder

### Evaluation pipeline attributes in `BasicSoftware`

***

### Questions

 - What's a batch? I've seen this word used in variables and method names in the algos and softwares classes but I don't
    understand what it is or how it's used.
    *possible answer* : a batch designates a batch of data files used for the software evaluation pipeline.
 - The `dominate()` method of the `AbstractAlgorithm` class seems to be used for comparing fitness results but I can't
    understand how it does it just by reading at the code.
 - what are the caches used for?
 

### Todo
 - continue elaborating on use of the strategy design pattern 
 - read on algorithm evolution techniques : start with genetic programming and try to find a new one to implement 
    myself

### Bibliography

 - The [Refactoring guru](https://refactoring.guru/design-patterns) website's section on design pattern gives a quick
    and strait to the point overview on a lot of widely used design patterns, allowing me to efficiently compare 
    the existing code and my diagrams with them
 - "*Head First Design pattern 2nd Edition*" by Eric Freeman and Elisabeth Robson, is a book going into details 
    describing the most currently used design patterns in software engineering. 