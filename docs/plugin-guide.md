# T++ Plugin Guide (V3)

T++ plugins are JSON files that can add keywords, source rewrites, and AST transforms.

## Minimal Plugin

```json
{
  "name": "demo-plugin",
  "version": "1.0.0",
  "keywords": [
    { "phrase": "announce", "template": "say {rest}" }
  ]
}
```

## Metadata

Required for full V3 behavior:

- name
- version

Optional:

- dependencies: list of plugin names
- keywords: phrase/template entries
- transforms: builtin AST transforms
- python_hooks: safe Python AST hooks

## Builtin AST Transform

Current builtin transform:

- rename_function

Example:

```json
{
  "type": "rename_function",
  "from": "legacy_add",
  "to": "add"
}
```

## Python Hooks (Sandboxed Rule)

Python transform hooks must be under the tpp_plugins namespace.

Example:

```json
{
  "python_hooks": [
    {
      "module": "tpp_plugins.my_transform",
      "callable": "transform"
    }
  ]
}
```

The callable must accept Program and return Program or None.

## CLI

Install plugin:

```powershell
tpp plugin install examples/sample_plugin.json
```

Load plugin when running:

```powershell
tpp run examples/plugin_demo.tpp --plugin examples/sample_plugin.json
```

List installed plugins:

```powershell
tpp plugin list
```

By default, installed plugins go to:

- ~/.tpp/plugins
