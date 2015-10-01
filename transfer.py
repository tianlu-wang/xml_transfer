__author__ = 'koala'
import os
import StringIO

from lxml import etree


class Tree(object):
    """
    Abstract base class for classes representing annotation documents.

    Supports both reading from and writing to XML.

    Inputs
    ------
    tree : lxml.etree.ElementTree
        ElementTree representing the XML document.

    Attributes
    ----------
    xml_version : str
        XML version of document.

    doc_type : str
        XML document type declaration.

    doc_id : str
        Document id.

    lang : lang
        Document language.
    """
    def __init__(self, tree):
        self.tree = tree
        self.xml_version = self.tree.docinfo.xml_version
        self.doc_type = self.tree.docinfo.doctype
        doc_elem = self.tree.find('//DOC')
        self.doc_id = doc_elem.get('id')
        self.lang = doc_elem.get('lang')
        if self.lang is None:
            self.lang = ''  # some version can have no lang attribute

    def write_to_file(self, xmlf):
        """
        write document to file as XML in the correct format
        :param xmlf: output file for XML
        :return:
        """
        self.tree.write(xmlf, encoding='utf-8', pretty_print=True, xml_declaration=True)


class LTFDocument(Tree):
    """
    supports reading/writing of LCTL text format (LTF) files.
     Inputs
    ------
    xmlf : str
        LTF XML file to read.

    Attributes
    ----------
    tree : lxml.etree.ElementTree
        ElementTree representing the XML document.

    xml_version : str
        XML version of document.

    doc_type : str
        XML document type declaration.

    doc_id : str
        Document id.

    lang : lang
        Document language.
    """
    def __init__(self, xmlf, new):
        if new is False:
            tree = etree.parse(xmlf)
            super(LTFDocument, self).__init__(tree)
        else:
            tree = etree.parse('./data/ltf_template.xml')
            super(LTFDocument, self).__init__(tree)

    def segments(self):
        """Lazily generate segments present in LTF document.

        Outputs
        -------
        segments : lxml.etree.ElementTree generator
            Generator for segments, each represented by an ElementTree.
        """
        for segment in self.tree.xpath('//SEG'):
            yield segment

    def tokenized(self):
        """Extract tokens.

        All returned indices assume 0-indexing.
        Outputs
        -------
        tokens : list of str
            Tokens.

        token_ids : list of str
            Token ids.

        token_onsets : list of int
            Character onsets of tokens.

        token_offsets : list of int
            Character offsets of tokens.
        """
        tokens = []
        token_ids = []
        token_onsets = []
        token_offsets = []
        for seg_ in self.segments():
            for token_ in seg_.xpath('.//TOKEN'):
                tokens.append(token_.text)
                token_ids.append(token_.get('id'))
                token_onsets.append(token_.get('start_char'))
                token_offsets.append(token_.get('end_char'))
        tokens = [' ' if token is None else token for token in tokens]
        token_onsets = [token_onset if token_onset is None else int(token_onset) for token_onset in token_onsets]
        token_offsets = [token_offset if token_offset is None else int(token_offset) for token_offset in token_offsets]
        return tokens, token_ids, token_onsets, token_offsets

    def text(self):
        """Return original text of document.
        """
        text = [elem.text for elem in self.tree.xpath('//ORIGINAL_TEXT')]
        text = u' '.join(text)
        return text


class LAFDocument(Tree):
    """Supports reading/writing of LCTL annotation format (LAF) files.

    Inputs
    ------
    xmlf : str, optional
        LAF XML file to read. If not provided, the document will be initialized
        from supplied mentions.

    mentions : list of tuples, optional
        List of mention tuples. For format, see mentions method docstring.

    lang : str, optional
        Document language.

    doc_id : str, optional
        Document id.

    Attributes
    ----------
    tree : lxml.etree.ElementTree
        ElementTree representing the XML document.

    xml_version : str
        XML version of document.

    doc_type : str
        XML document type declaration.

    doc_id : str
        Document id.

    lang : str
        Document language.
    """
    def __init__(self, xmlf=None, mentions=None, lang=None, doc_id=None):
        def xor(a, b):
            return a + b == 1
        assert(xor(xmlf is not None, mentions is not None))
        if not xmlf is None:
            tree = etree.parse(xmlf)
        else:
            base_xml = """<?xml version='1.0' encoding='UTF-8'?>
                          <!DOCTYPE LCTL_ANNOTATIONS SYSTEM "laf.v1.2.dtd">
                          <LCTL_ANNOTATIONS/>
                       """

            # Create and set attributes on root node.
            tree = etree.parse(StringIO.StringIO(base_xml))
            root = tree.getroot()
            root.set('lang', lang)

            # Create and set attributes on doc node.
            doc = etree.SubElement(root, 'DOC')
            doc.set('id', doc_id)
            doc.set('lang', lang)

            # And for all the mentions.
            for entity_id, type, extent, start_char, end_char in mentions:
                # <ANNOTATION>...</ANNOTATION
                annotation = etree.SubElement(doc, 'ANNOTATION')
                annotation.set('id', entity_id)
                annotation.set('task', 'NE')  # move to constant or arg?
                annotation.set('type', type)
                # <EXTENT>...</EXTENT>
                extent_elem = etree.SubElement(annotation, 'EXTENT')
                extent_elem.text = extent
                extent_elem.set('start_char', str(start_char))
                extent_elem.set('end_char', str(end_char))

        super(LAFDocument, self).__init__(tree)

    def mentions(self):
        """Extract mentions.

        Returns a list of mention tuples, each of the form:

        (entity_id, tag, extent, start_char, end_char)
        where entity_id is the entity id, tag the annotation tag,
        extent the text extent (a string) of the mention in the underlying
        RSD file, start_char the character onset (0-indexed) of the mention,
        and end_char the character offset (0-indexed) of the mention.
        """
        mentions = []
        for mention_ in self.tree.xpath('//ANNOTATION'):
            entity_id = mention_.get('id')
            type = mention_.get('type')
            extent = mention_.xpath('EXTENT')[0]
            start_char = int(extent.get('start_char'))
            end_char = int(extent.get('end_char'))

            mention = [entity_id,
                       type,
                       extent,
                       start_char,
                       end_char]
            mentions.append(mention)

        return mentions


def load_doc(xmlf, cls, new=False):
    """Parse xml file and return document.

    This is a helper function intended to help debugging.

    Inputs
    ------
    xmlf : str
        XML file to open.

    cls : Tree class
        Subclass of Tree.

    logger : logging.Logger
        Logger instance.
    """
    try:
        print xmlf
        # assert(os.path.exists(xmlf))
        if not os.path.exists(xmlf):
            f = open(xmlf, 'w+')
            doc = cls(xmlf, new)
            f.close()
        else:
            doc = cls(xmlf, new)
    except KeyError:
        doc = None
    return doc

if __name__ == '__main__':
    ltf_path = './data/NW_AMI_HAU_006001_20141128.ltf.xml'
    laf_path = './data/NW_AMI_HAU_006001_20141128.ltf.xml'
    ltf_split_result_path = './data/ltf_split_result'
    laf_split_result_path = './data/laf_split_result'

    ltf_doc = load_doc(ltf_path, LTFDocument)
    segments = ltf_doc.segments()
    for segment in segments:
        ltf_temp = load_doc(ltf_split_result_path+'/NW_AMI_HAU_006001_20141128'+'_'+segment.get('id')+'ltf.xml', LTFDocument, True)
        ltf_temp.tree.xpath('DOC')[0][0][0] = segment

        ltf_temp.write_to_file




