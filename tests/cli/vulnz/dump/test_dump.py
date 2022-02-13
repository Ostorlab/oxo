"""Unittest for vulnz dump command."""
from unittest import mock
import json
import csv


from click.testing import CliRunner

from ostorlab.cli import rootcli
from ostorlab.runtimes.local.models import models


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db_cli.sqlite')
def testVulnzDump_whenOptionsAreValid_jsonOutputFileIsCreated(tmp_path):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a json file with the vulnerabilities.

    tmp_path : pytest fixture for temporary paths & files.
    """
    # breakpoint()
    runner = CliRunner()
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)

    output_file = tmp_path / 'output.json'
    result = runner.invoke(rootcli.rootcli,
                           ['vulnz', 'dump', '-s', str(vuln_db.scan_id), '-o', output_file, '-f', 'json'])
    data = json.loads(output_file.read_bytes())

    assert result.exception is None
    assert 'Vulnerabilities saved' in result.output
    assert len(list(tmp_path.iterdir())) == 1
    assert data[str(vuln_db.id)]['risk_rating'] == 'High'


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db_cli.sqlite')
def testVulnzDump_whenOptionsAreValid_csvOutputFileIsCreated(tmp_path):
    """Test ostorlab vulnz dump command with correct commands and options.
    Should create a csv file with the vulnerabilities.

    tmp_path : pytest fixture for temporary paths & files.
    """

    runner = CliRunner()
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')
    vuln_db = models.Vulnerability.create(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HIGH',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)

    output_file = tmp_path / 'output.csv'
    result = runner.invoke(rootcli.rootcli,
                           ['vulnz', 'dump', '-s', str(vuln_db.scan_id), '-o', output_file,  '-f', 'csv'])
    with open(output_file, 'r', encoding='utf-8') as file:
        csvreader = csv.reader(file)
        header = next(csvreader)
        data = []
        for row in csvreader:
            data.append(row)

    assert result.exception is None
    assert 'Vulnerabilities saved' in result.output
    assert len(list(tmp_path.iterdir())) == 1
    assert header == ['id', 'title', 'risk_rating', 'cvss_v3_vector', 'short_description']
    assert data[0][2] == 'High'


@mock.patch('ostorlab.runtimes.local.models.models.ENGINE_URL', 'sqlite:////tmp/ostorlab_db_cli.sqlite')
def testVulnzDumpInOrderOfSeverity_whenOptionsAreValid_jsonOutputFileIsCreated(tmp_path):
    runner = CliRunner()
    models.Database().create_db_tables()
    create_scan_db = models.Scan.create('test')

    vuln_db = models.Vulnerability.create(title='MyVuln', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'HARDENING',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)
    _ = models.Vulnerability.create(title='MyVuln2', short_description= 'Xss', description= 'Javascript Vuln',
    recommendation= 'Sanitize data', technical_detail= 'a=$input', risk_rating= 'LOW',
    cvss_v3_vector= '5:6:7', dna= '121312', scan_id=create_scan_db.id)


    output_file = tmp_path / 'output.json'
    result = runner.invoke(rootcli.rootcli,
                           ['vulnz', 'dump', '-s', str(vuln_db.scan_id), '-o', output_file, '-f', 'json'])
    data = json.loads(output_file.read_bytes())

    assert result.exception is None
    assert 'Vulnerabilities saved' in result.output
    assert data[list(data)[0]]['risk_rating'] == 'Low' and data[list(data)[1]]['risk_rating'] == 'Hardening'
