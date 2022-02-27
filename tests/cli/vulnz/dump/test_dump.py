"""Unittest for vulnz dump command."""
import json
import csv
import pathlib

from click.testing import CliRunner

from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


def testVulnzDump_whenOptionsAreValid_jsonOutputFileIsCreated(mocker, tmpdir, db_engine_path):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a json file with the vulnerabilities.

    tmpdir : pytest fixture for temporary paths & files.
    """

    runner = CliRunner()
    mocker.patch.object(models, 'ENGINE_URL', db_engine_path)
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create(title='test', asset='android')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description='Xss', description='Javascript Vuln',
                                          recommendation='Sanitize data', technical_detail='a=$input',
                                          risk_rating='HIGH',
                                          cvss_v3_vector='5:6:7', dna='121312', scan_id=create_scan_db.id)
    output_file = pathlib.Path(tmpdir) / 'output.json'
    result = runner.invoke(rootcli.rootcli,
                           ['vulnz', 'dump', '-s', str(vuln_db.scan_id), '-o', str(output_file), '-f', 'json'])
    assert result.exception is None
    assert 'Vulnerabilities saved' in result.output
    with output_file.open('r', encoding='UTF-8') as f:
        data = json.loads(f.read())
        assert data[str(vuln_db.id)]['risk_rating'] == 'High'


def testVulnzDump_whenOptionsAreValid_csvOutputFileIsCreated(mocker, tmpdir, db_engine_path):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a csv file with the vulnerabilities.

    tmpdir : pytest fixture for temporary paths & files.
    """

    runner = CliRunner()
    mocker.patch.object(models, 'ENGINE_URL', db_engine_path)
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create(title='test', asset='Android')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description='Xss', description='Javascript Vuln',
                                          recommendation='Sanitize data', technical_detail='a=$input',
                                          risk_rating='HIGH',
                                          cvss_v3_vector='5:6:7', dna='121312', scan_id=create_scan_db.id)

    output_file = pathlib.Path(tmpdir) / 'output.csv'

    result = runner.invoke(rootcli.rootcli,
                           ['vulnz', 'dump', '-s', str(vuln_db.scan_id), '-o', str(output_file), '-f', 'csv'])
    with output_file.open('r', encoding='utf-8') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        data = []
        for row in csvreader:
            if row:
                data.append(row)

    assert result.exception is None
    assert 'Vulnerabilities saved' in result.output
    assert header == ['id', 'title', 'risk_rating', 'cvss_v3_vector', 'short_description']
    assert data[0][2] == 'High'


def testVulnzDumpInOrderOfSeverity_whenOptionsAreValid_jsonOutputFileIsCreated(mocker, tmpdir, db_engine_path):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a json file with the vulnerabilities, ordered by the risk severity.

    tmpdir : pytest fixture for temporary paths & files.
    """
    runner = CliRunner()
    mocker.patch.object(models, 'ENGINE_URL', db_engine_path)
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create(title='test', asset='Android')

    vuln_db = models.Vulnerability.create(title='MyVuln', short_description='Xss', description='Javascript Vuln',
                                          recommendation='Sanitize data', technical_detail='a=$input',
                                          risk_rating='HARDENING',
                                          cvss_v3_vector='5:6:7', dna='121312', scan_id=create_scan_db.id)
    _ = models.Vulnerability.create(title='MyVuln2', short_description='Xss', description='Javascript Vuln',
                                    recommendation='Sanitize data', technical_detail='a=$input', risk_rating='LOW',
                                    cvss_v3_vector='5:6:7', dna='121312', scan_id=create_scan_db.id)

    output_file = pathlib.Path(tmpdir) / 'output.json'
    result = runner.invoke(rootcli.rootcli,
                           ['vulnz', 'dump', '-s', str(vuln_db.scan_id), '-o', str(output_file), '-f', 'json'])
    with output_file.open('r', encoding='UTF-8') as f:
        data = json.loads(f.read())
        assert result.exception is None
        assert 'Vulnerabilities saved' in result.output
        assert data[list(data)[0]]['risk_rating'] == 'Low' and data[list(data)[1]]['risk_rating'] == 'Hardening'
