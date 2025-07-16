import abc

from magpie.core import AbstractModel


class AbstractRIDModel(AbstractModel):
    @abc.abstractmethod
    def do_replace(self, ref_model, target_dest, target_orig):
        pass

    @abc.abstractmethod
    def do_insert(self, ref_model, target_dest, target_orig):
        pass

    @abc.abstractmethod
    def do_delete(self, target):
        pass
