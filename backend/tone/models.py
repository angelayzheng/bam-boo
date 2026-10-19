from django.db import models


class ToneVector(models.Model):
    """A single word and its ConceptNet Numberbatch embedding vector.

    The vector is stored as a BLOB of little-endian 32-bit floats so that it
    can be loaded directly into a Python ``array('f', ...)`` without parsing.
    """

    word = models.CharField(max_length=200, unique=True, db_index=True)
    vector = models.BinaryField()

    class Meta:
        db_table = "tone"

    def __str__(self):
        return self.word
