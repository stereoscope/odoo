import json
import base64
from odoo.addons.http_routing.models.ir_http import slug
from odoo.tools import file_open
from scratching.app import run

def execute(env):
    with file_open('documents_ocr/tests/resources/test.pdf', 'rb') as f:
        _test_pdf_content = f.read()

    assert _test_pdf_content is not None

    test_pdf_as_base64 = base64.b64encode(_test_pdf_content)

    doc = env['documents.document'].browse(28713)

    attachment = env['ir.attachment'].create({
        'datas': test_pdf_as_base64,
        'name': 'test2attach.pdf',
        'res_model': 'documents.document',
        'res_id': 0,
    })

    document = env['documents.document'].create({
        'folder_id': doc.folder_id.id,
        'name': 'test2.pdf',
        'attachment_id': attachment.id,
    })


if __name__ == '__main__':
    run(execute, commit_changes=False)
