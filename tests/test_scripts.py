from material_studio_mcp_server.runner import extract_tagged_json, perl_string
from material_studio_mcp_server.scripts import (
    forcite_geometry_optimization_script,
    import_export_script,
    validate_materialscript,
)


def test_extract_tagged_json() -> None:
    output = 'noise\n__MATERIAL_STUDIO_MCP_JSON_BEGIN__\n{"ok": true}\n__MATERIAL_STUDIO_MCP_JSON_END__\n'
    assert extract_tagged_json(output) == {"ok": True}


def test_perl_string_escapes_backslash_and_quote() -> None:
    assert perl_string(r"C:\a\b's.xsd") == r"'C:\\a\\b\'s.xsd'"


def test_import_export_script_uses_materialscript() -> None:
    script = import_export_script(r"C:\in.cif", r"C:\out.xsd")
    assert "use MaterialsScript qw(:all);" in script
    assert "Documents->Import" in script
    assert "$doc->Export" in script


def test_forcite_script_contains_expected_task() -> None:
    script = forcite_geometry_optimization_script(
        r"C:\in.xsd",
        r"C:\out.xsd",
        forcefield="COMPASS",
        quality="Medium",
        charge_assignment="Forcefield assigned",
        max_iterations=500,
        convergence="Medium",
    )
    assert "Modules->Forcite->GeometryOptimization->Run($doc)" in script
    assert "CurrentForcefield => 'COMPASS'" in script


def test_validate_materialscript_requires_import() -> None:
    result = validate_materialscript("print 'hello';")
    assert result["valid"] is False
    assert result["errors"]
