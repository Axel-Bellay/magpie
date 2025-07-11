import abc

from magpie.core import BasicModel


class AbstractRIDModel(BasicModel):
    @abc.abstractmethod
    def do_replace(self, ref_model, target_dest, target_orig):
        pass

    @abc.abstractmethod
    def do_insert(self, ref_model, target_dest, target_orig):
        pass

    @abc.abstractmethod
    def do_delete(self, target):
        pass
