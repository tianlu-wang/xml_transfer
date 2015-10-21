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
    def __init__(self, xmlf, segment=None, doc_id=None):
        def xor(a, b):
            return a + b == 1
        assert(xor(xmlf is not None, segment is not None))
        if not xmlf is None:
            tree = etree.parse(xmlf)
        else:
            base_xml = """<?xml version='1.0' encoding='UTF-8'?>
                          <!DOCTYPE LCTL_TEXT SYSTEM "ltf.v1.5.dtd">
                          <LCTL_TEXT/>
                       """

            # base_xml = """<?xml version='1.0' encoding='UTF-8'?>
            #               <!DOCTYPE LCTL_TEXT SYSTEM "ltf.v1.5.dtd">
            #               <LCTL_TEXT/>
            #            """
            # Create and set attributes on root node.
            tree = etree.parse(StringIO.StringIO(base_xml))
            root = tree.getroot()

            # Create and set attributes on doc node.
            doc = etree.SubElement(root, 'DOC')
            doc.set('id', doc_id)

            text = etree.SubElement(doc, 'TEXT')
            seg = etree.SubElement(text, 'SEG')
            text.replace(seg, segment)
            # seg.set('id', segment.get('id'))
            # seg.set('start_char', segment.get('start_char'))
            # seg.set('end_char', segment.get('end_char'))
            # original_text = etree.SubElement(seg, 'ORIGINAL_TEXT')
            # original_text.text = segment.find('ORIGINAL_TEXT').text
            # tokens = segment.xpath('.//TOKEN')
            # seg.extend(tokens)
            # print etree.tostring(tree, pretty_print=True)


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
                # <ANNOTATION>...</ANNOTATION>
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

    def annotations(self):
        """Lazily generate annotations present in LAF document.
        Outputs
        -------
        annotations : lxml.etree.ElementTree generator
            Generator for annotations, each represented by an ElementTree.
        """
        for annotation in self.tree.xpath('//ANNOTATION'):
            yield annotation
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


def load_doc(xmlf, cls):
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
        assert(os.path.exists(xmlf))
        doc = cls(xmlf)
    except KeyError:
        doc = None
    return doc

if __name__ == '__main__':
    ltf_split_result_path = './data/hausa_test/split'
    #laf_split_result_path = './data/hausa_test'

    ltf_dir = './data/hausa_test/test'
    #laf_dir = './data/hausa_test'
    ltf_files = []
    #laf_files = []
    for root, dirs, files in os.walk(ltf_dir):
        for f in files:
            if f.find('ltf') > 0:
                temp = ltf_dir+'/'+f
                ltf_files.append(temp)
                #laf_files.append(temp.replace('ltf', 'laf'))  # search every file in ltf and laf
    # print 'this is ltf_files:'
    # print ltf_files
    # print laf_files

    for k in range(len(ltf_files)):
    # for k in range(1):
        print 'k: ' + str(k)
        ltf_path = ltf_files[k]
        #laf_path = laf_files[k]
        ltf_doc = load_doc(ltf_path, LTFDocument)
        #laf_doc = load_doc(laf_path, LAFDocument)
        segments = ltf_doc.segments()   # load the ltf and laf files and the segments in ltf file
        j = 0
        for segment in segments:
            # print '************'
            # print j
            # print '============'
            ltff = ltf_split_result_path+'/'+ ltf_doc.doc_id +'_'+segment.get('id')+'.'+'ltf.xml'
            #laff = laf_split_result_path+'/NW_AMI_HAU_006001_20141128'+'_'+segment.get('id')+'.'+'laf.xml'
            ltf_temp = LTFDocument(xmlf=None, segment=segment, doc_id=ltf_doc.doc_id+'_'+segment.get('id'))
            ltf_temp.write_to_file(ltff)

            #######for debug
            # test = load_doc(ltff, LTFDocument)
            # print test.doc_id
            # tmp = test.segments()
            # for item in tmp:
            #     print item.get('id')
            #     print '1'
            ##########
            # mentions = []
            # i = 0
            # annotations = laf_doc.annotations()
            # for annotation in annotations:
            #     print 'this is J==================================================='
            #     print j
            #     start_char = annotation.find('EXTENT').get('start_char')
            #     # print '======'
            #     # print start_char
            #     # print '========'
            #     end_char = annotation.find('EXTENT').get('end_char')
            #     # print '======'
            #     # print end_char
            #     # print '========'
            #     start_char = annotation.getchildren()[0].get('start_char')
            #     end_char = annotation.getchildren()[0].get('end_char')
            #     print i
            #     print 'start' + start_char + 'end' + end_char
            #     print 'sstart' + segment.get('start_char') + 'send' + segment.get('end_char')
            #     if int(start_char) >= int(segment.get('start_char')) and int(end_char) <= int(segment.get('end_char')):
            #         print 'OK'
            #         entity_id = annotation.get('id')
            #         type = annotation.get('type')
            #         extent = annotation.xpath('EXTENT')[0]
            #         start_char = int(extent.get('start_char'))
            #         end_char = int(extent.get('end_char'))
            #         extent_text = extent.text
            #
            #         mention = [entity_id,
            #                    type,
            #                    extent_text,
            #                    start_char,
            #                    end_char]
            #         mentions.append(mention)
            #     else:
            #         pass
            #     i += 1
            # print mentions
            # laf_temp = LAFDocument(xmlf=None, mentions=mentions, lang=laf_doc.lang, doc_id=ltf_doc.doc_id+'_'+segment.get('id'))
            # laf_temp.write_to_file(laff)
            # print laf_temp.mentions()
            # j+=1


                





