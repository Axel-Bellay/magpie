import magpie.utils
from magpie.core import AbstractEdit

from ..abstract_rid_model import AbstractRIDModel


class LineDeletionEdit(AbstractEdit):
    @classmethod
    def auto_create(cls, ref):
        target = ref.random_model(AbstractRIDModel).random_target('line')
        if not target:
            return None
        return cls(target)

    def apply(self, ref, variant):
        model = variant.models[self.target[0]]
        return model.do_delete(self.target)

magpie.utils.known_edits.append(LineDeletionEdit)

class LineReplacementEdit(AbstractEdit):
    @classmethod
    def auto_create(cls, ref):
        target, ingredient = ref.random_targets(AbstractRIDModel, 'line', 'line')
        if not (target and ingredient):
            return None
        return cls(target, ingredient)

    def apply(self, ref, variant):
        ingredient = self.data[0]
        ref_model = ref.models[ingredient[0]]
        model = variant.models[self.target[0]]
        return model.do_replace(ref_model, self.target, ingredient)

magpie.utils.known_edits.append(LineReplacementEdit)

class LineInsertionEdit(AbstractEdit):
    @classmethod
    def auto_create(cls, ref):
        target, ingredient = ref.random_targets(AbstractRIDModel, '_inter_line', 'line')
        if not (target and ingredient):
            return None
        return cls(target, ingredient)

    def apply(self, ref, variant):
        ingredient = self.data[0]
        ref_model = ref.models[ingredient[0]]
        model = variant.models[self.target[0]]
        return model.do_insert(ref_model, self.target, ingredient)

magpie.utils.known_edits.append(LineInsertionEdit)
