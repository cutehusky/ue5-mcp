"""Geometry Script Dynamic Mesh tools end to end through the MCP dispatcher: prepare, restart, verify.

Usage: smoke_geometry_script_live.py prepare|verify|cleanup. On a scratch map, creates an actor with two Dynamic Mesh
components (Target, Tool) and drives every Geometry Script MCP tool. Each mutating tool is first called as a dry run
(the mesh fingerprint must not change), then for real; results are checked against native measurements. A duplicated
Static Mesh asset is read from and written to. The final meshes and the asset must survive a cold editor restart.
"""
import asyncio
import json
import sys

import httpx
from smoke_animation_curves_live import PROJECT, Api

sys.path.insert(0, str(PROJECT / 'Plugins' / 'UE5_MCP' / 'Python' / 'MCP'))
# mcp_server parses sys.argv on import; hide this script's command from it.
COMMAND, sys.argv[1:] = (sys.argv[1] if len(sys.argv) > 1 else 'prepare'), []
import mcp_server

BASE = 'http://127.0.0.1:8080'
MAP = '/Game/UE5MCP_Test/MCP_Geometry'
SM_PKG = '/Game/UE5MCP_Test/SM_MCP_Geo'
SM = SM_PKG + '.SM_MCP_Geo'
STATE = PROJECT / 'Saved' / 'UE5MCP_Test' / 'geometry_script.json'
T0 = {'Translation': {'X': 0, 'Y': 0, 'Z': 0}, 'Rotation': {'X': 0, 'Y': 0, 'Z': 0, 'W': 1}, 'Scale3D': {'X': 1, 'Y': 1, 'Z': 1}}


def frame(z=50, x=0, y=0, rot=None):
    return {**T0, 'Translation': {'X': x, 'Y': y, 'Z': z}, 'Rotation': rot or T0['Rotation']}


class Geo:
    def __init__(self):
        self.tools = None
        self.failures = []
        self.passed = []

    async def raw(self, name, args):
        result = await mcp_server.mcp.call_tool(name, args)
        blocks = result[0] if isinstance(result, tuple) else result
        text = ''.join(b.text for b in blocks if hasattr(b, 'text'))
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = {'errorMessage': 'non-JSON: ' + text[:300]}
        return payload

    async def call(self, name, args):
        p = await self.raw(name, args)
        if isinstance(p, dict) and 'errorMessage' in p:
            raise AssertionError((name, p['errorMessage'][:400]))
        return p

    def ident(self, comp):
        return dict(actor_path=self.actor, component_path=self.actor + '.' + comp, mesh_path=self.actor + '.' + comp + '.DynamicMesh')

    async def fp(self, comp='Target'):
        m = await self.call('measure_geometry_script_mesh', self.ident(comp))
        return {k: (round(v, 2) if isinstance(v, float) else v) for k, v in m.items() if k != 'scope'}

    async def topo(self, comp='Target', span=256):
        return await self.call('inspect_geometry_script_topology', dict(self.ident(comp), id_span=span))

    async def tris(self, ids, comp='Target'):
        t = {x['id']: x['vertices'] for x in (await self.topo(comp))['triangles']}
        return [t.get(i, [-1, -1, -1]) for i in ids]

    async def step(self, tool, comp='Target', check=None, changes=True, **args):
        """Dry run must leave the mesh alone; the real call must succeed and pass the check."""
        name = tool
        try:
            props = self.tools[name].inputSchema['properties']
            full = {**(self.ident(comp) if 'mesh_path' in props else {}), **args}
            if 'dry_run' in props and 'mesh_path' not in props:
                d = await self.call(name, {**full, 'confirm': True, 'dry_run': True})
                assert d.get('dry_run') is True, (name, str(d)[:200])
                r = await self.call(name, {**full, 'confirm': True, 'dry_run': False})
            elif 'dry_run' in props:
                before = await self.fp(comp)
                d = await self.call(name, {**full, 'confirm': True, 'dry_run': True})
                assert d.get('dry_run', True) is True, (name, 'dry run flag', str(d)[:200])
                assert await self.fp(comp) == before, (name, 'dry run changed mesh')
                r = await self.call(name, {**full, 'confirm': True, 'dry_run': False})
                if changes:
                    assert await self.fp(comp) != before or name in NO_FP_CHANGE, (name, 'real call left measurements unchanged', str(r)[:300])
            else:
                r = await self.call(name, full)
            if check:
                res = check(r)
                if asyncio.iscoroutine(res):
                    await res
            self.passed.append(name)
            return r
        except Exception as e:  # collect and continue so one run reports every failing tool
            self.failures.append((name, repr(e)[:600]))
            print('FAIL', name, repr(e)[:600], flush=True)
            return None

    async def reset(self, comp='Target', shape='box'):
        await self.call('clear_geometry_script_mesh', {**self.ident(comp), 'confirm': True})
        if shape == 'box':
            await self.call('append_geometry_script_box', {**self.ident(comp), 'dimensions': {'X': 100, 'Y': 100, 'Z': 100}, 'transform': T0, 'confirm': True})
        else:
            await self.call('append_geometry_script_sphere', {**self.ident(comp), 'transform': frame(0), 'radius': 60, 'confirm': True})


# Tools whose real effect is on attributes the measurement fingerprint does not cover.
NO_FP_CHANGE = {
    'recompute_geometry_script_normals', 'split_geometry_script_normals', 'compute_geometry_script_tangents', 'project_geometry_script_uvs',
    'set_geometry_script_uv_channel_count', 'clear_geometry_script_uv_channel', 'set_geometry_script_material_ids', 'set_geometry_script_triangle_material_id',
    'remap_geometry_script_material_ids', 'compact_geometry_script_mesh', 'set_geometry_script_normal_mode', 'transform_geometry_script_uvs',
    'copy_geometry_script_uv_channel', 'set_geometry_script_triangle_uvs', 'generate_geometry_script_polygroups', 'auto_generate_geometry_script_uvs',
    'repack_geometry_script_uvs', 'generate_geometry_script_collision', 'clear_geometry_script_collision', 'set_geometry_script_material',
    'set_geometry_script_vertex_color', 'set_geometry_script_selected_vertex_color', 'set_geometry_script_selected_polygroup',
    'set_geometry_script_selected_material_ids', 'set_geometry_script_polygroup_layer_count', 'copy_geometry_script_polygroup_layer',
    'add_geometry_script_named_polygroup_layer', 'clear_geometry_script_polygroup_layer', 'scale_geometry_script_texel_density',
    'recompute_geometry_script_uvs', 'remove_geometry_script_unused_vertices', 'weld_geometry_script_edges', 'repair_geometry_script_boundaries',
    'add_geometry_script_vertex', 'remove_geometry_script_small_components', 'simplify_geometry_script_regions', 'write_geometry_script_mesh_to_static_mesh',
    'generate_static_mesh_collision_from_geometry_script_mesh', 'flip_geometry_script_selected_normals', 'copy_static_mesh_to_geometry_script_mesh',
}


def need(cond, *msg):
    assert cond, msg


async def world(g):
    comps = (await g.call('inspect_geometry_script_world_meshes', {}))['components']
    return {c['component_path'].rsplit('.', 1)[1]: c for c in comps}


async def run_prepare(api):
    g = Geo()
    g.tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
    cleanup(api)
    assert api.call('POST', '/worlds/create', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bSave': True})['success']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    g.actor = httpx.post(BASE + '/editor/actors/spawn', json={'ActorClass': '/Script/Engine.Actor'}, timeout=60).text
    assert g.actor.startswith(MAP), g.actor
    httpx.post(BASE + '/assets/duplicate', json={'AssetPath': '/Engine/BasicShapes/Cube.Cube', 'DestinationPath': SM_PKG}, timeout=180)

    # Components.
    for comp in ('Target', 'Tool'):
        await g.step('add_geometry_script_mesh_component', component_name=comp, actor_path=g.actor, changes=False)
    w = await world(g)
    need({'Target', 'Tool'} <= set(w), w.keys())
    bad = await g.raw('add_geometry_script_mesh_component', dict(actor_path=g.actor, component_name='Target', confirm=True))
    need('errorMessage' in bad, 'duplicate component name accepted')

    # Primitives and whole-mesh transform.
    async def counts(v, t):
        f = await g.fp()
        need((f['vertex_count'], f['triangle_count']) == (v, t), f)
    await g.step('append_geometry_script_box', dimensions={'X': 100, 'Y': 100, 'Z': 100}, transform=T0, check=lambda r: counts(8, 12))
    await g.step('append_geometry_script_sphere', transform=frame(200), radius=40, steps_phi=6, steps_theta=8)
    await g.step('append_geometry_script_cylinder', transform=frame(0, x=200), radius=30, height=80, radial_steps=8)
    await g.step('transform_geometry_script_mesh', transform={**T0, 'Scale3D': {'X': 2, 'Y': 2, 'Z': 2}})
    bad = await g.raw('transform_geometry_script_mesh', dict(g.ident('Target'), transform={**T0, 'Scale3D': {'X': 0, 'Y': 1, 'Z': 1}}, confirm=True))
    need('errorMessage' in bad, 'zero scale accepted')
    await g.step('validate_geometry_script_mesh', check=lambda r: need(r.get('valid', r.get('is_valid', True)), r))
    await g.step('inspect_geometry_script_edges', check=lambda r: need(r['edges'], r))
    await g.step('clear_geometry_script_mesh', check=lambda r: counts(0, 0))

    # Normals, tangents, UVs on a box.
    await g.reset()
    await g.step('recompute_geometry_script_normals')
    await g.step('split_geometry_script_normals', opening_angle=45)
    await g.step('set_geometry_script_normal_mode', normal_mode='Repair')
    await g.step('compute_geometry_script_tangents')
    await g.step('inspect_geometry_script_normals', check=lambda r: need(r.get('elements') or r.get('triangles'), str(r)[:300]))
    await g.step('set_geometry_script_uv_channel_count', count=3)
    await g.step('project_geometry_script_uvs', transform=T0, projection='Box')
    await g.step('copy_geometry_script_uv_channel', source_uv_layer=0, destination_uv_layer=1)
    await g.step('clear_geometry_script_uv_channel', uv_layer=2)
    await g.step('transform_geometry_script_uvs', scale_x=2, scale_y=2, rotation_degrees=30)
    tri0 = (await g.tris([0]))[0]
    await g.step('set_geometry_script_triangle_uvs', triangle_id=0, expected_vertices=tri0, uv0=[0, 0], uv1=[1, 0], uv2=[0, 1])
    bad = await g.raw('set_geometry_script_triangle_uvs', dict(g.ident('Target'), triangle_id=0, expected_vertices=[tri0[1], tri0[0], tri0[2]], uv0=[0, 0], uv1=[1, 0], uv2=[0, 1], confirm=True))
    need('errorMessage' in bad, 'stale triangle vertex order accepted')
    await g.step('inspect_geometry_script_uvs', check=lambda r: need(r.get('elements') or r.get('triangles'), str(r)[:300]))
    await g.step('measure_geometry_script_uvs')
    await g.step('auto_generate_geometry_script_uvs', uv_layer=1)
    await g.step('repack_geometry_script_uvs', uv_layer=1)
    await g.step('recompute_geometry_script_uvs', uv_layer=1)
    await g.step('scale_geometry_script_texel_density', uv_layer=0)

    # Vertex/triangle editing.
    await g.reset()
    t = await g.topo()
    v0 = t['vertices'][0]
    pos = dict(zip('XYZ', v0['position']))
    await g.step('set_geometry_script_vertex_position', vertex_id=v0['id'], expected_position=pos, position={**pos, 'Z': -20})
    bad = await g.raw('set_geometry_script_vertex_position', dict(g.ident('Target'), vertex_id=v0['id'], expected_position=pos, position=pos, confirm=True))
    need('errorMessage' in bad, 'stale vertex position accepted')
    await g.step('add_geometry_script_vertex', position={'X': 0, 'Y': 0, 'Z': 300}, check=lambda r: counts(9, 12))
    for p in ({'X': 100, 'Y': 0, 'Z': 300}, {'X': 0, 'Y': 100, 'Z': 300}):
        await g.call('add_geometry_script_vertex', {**g.ident('Target'), 'position': p, 'confirm': True})
    # A free-standing triangle on three new vertices (edges of the box already have two faces).
    await g.step('add_geometry_script_triangle', vertex_a=8, vertex_b=9, vertex_c=10, check=lambda r: counts(11, 13))
    new = (await g.tris([12]))[0]
    await g.step('delete_geometry_script_triangle', triangle_id=12, expected_a=new[0], expected_b=new[1], expected_c=new[2])
    await g.step('remove_geometry_script_unused_vertices', check=lambda r: counts(8, 12))
    sel = [0, 1]
    await g.step('delete_geometry_script_triangles', selected_triangles=sel, expected_vertices=await g.tris(sel), check=lambda r: counts(8, 10))
    await g.step('compact_geometry_script_mesh')
    await g.step('fill_geometry_script_holes', check=lambda r: counts(8, 12))
    await g.step('weld_geometry_script_edges')
    await g.step('repair_geometry_script_boundaries')

    # Materials.
    await g.reset()
    await g.step('set_geometry_script_material_ids', material_id=1)
    tri = (await g.tris([3]))[0]
    await g.step('set_geometry_script_triangle_material_id', triangle_id=3, expected_vertices=tri, expected_material_id=1, material_id=4)
    bad = await g.raw('set_geometry_script_triangle_material_id', dict(g.ident('Target'), triangle_id=3, expected_vertices=tri, expected_material_id=1, material_id=5, confirm=True))
    need('errorMessage' in bad, 'stale material ID accepted')
    await g.step('remap_geometry_script_material_ids', from_material_id=1, to_material_id=2)
    await g.step('set_geometry_script_selected_material_ids', selected_triangles=[5, 6], expected_vertices=await g.tris([5, 6]), material_id=3)
    await g.step('find_geometry_script_region_faces', filter_type='Material', filter_id=3, check=lambda r: need(sorted(x['id'] for x in r['triangles']) == [5, 6], r))
    mats = await g.step('inspect_geometry_script_materials', check=lambda r: need(r['material_count'] == 0, r))
    # Append slot 0 (index == count), then replace it; an empty expected path stands for the null slot.
    basic = '/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial'
    await g.step('set_geometry_script_material', material_index=0, expected_material_count=0, expected_material_path='', material_path=basic)
    bad = await g.raw('set_geometry_script_material', dict(g.ident('Target'), material_index=3, expected_material_count=1, expected_material_path='', material_path=basic, confirm=True))
    need('errorMessage' in bad, 'non-contiguous slot accepted')
    await g.step('set_geometry_script_material', material_index=0, expected_material_count=1, expected_material_path=basic,
                 material_path='/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial')
    await g.step('inspect_geometry_script_materials', check=lambda r: need(r['material_count'] == 1 and 'WorldGridMaterial' in str(r['materials']), r))

    # Polygroups.
    await g.step('generate_geometry_script_polygroups', mode='Components')
    await g.step('inspect_geometry_script_polygroups', check=lambda r: need(r.get('groups') or r.get('group_count'), str(r)[:300]))
    await g.step('set_geometry_script_polygroup_layer_count', layer_count=2)
    await g.step('add_geometry_script_named_polygroup_layer', name='Regions')
    await g.step('copy_geometry_script_polygroup_layer', source_layer=-1, destination_layer=0)
    await g.step('set_geometry_script_selected_polygroup', selected_triangles=[0, 1], expected_vertices=await g.tris([0, 1]), group_id=42, polygroup_layer=0)
    await g.step('find_geometry_script_region_faces', filter_type='Polygroup', filter_id=42, polygroup_layer=0)
    await g.step('clear_geometry_script_polygroup_layer', layer=1, clear_value=7)
    await g.step('simplify_geometry_script_regions', mode='Planar')

    # Vertex colors and normal flips.
    await g.step('set_geometry_script_vertex_color', red=0.5, green=0.25, blue=0, alpha=1)
    await g.step('set_geometry_script_selected_vertex_color', selected_triangles=[2], expected_vertices=await g.tris([2]), red=1, green=0, blue=0, create_seam=True)
    await g.step('inspect_geometry_script_vertex_colors', check=lambda r: need(r.get('elements') or r.get('triangles'), str(r)[:300]))
    await g.step('flip_geometry_script_normals')
    f = await g.fp()
    need(f['signed_volume'] < 0, 'flip did not reverse orientation', f)
    await g.step('flip_geometry_script_selected_normals', selected_triangles=[0], expected_vertices=await g.tris([0]))

    # Modeling operators.
    await g.reset()
    await g.step('extrude_geometry_script_mesh', distance=10, selected_triangles=[0, 1], expected_vertices=await g.tris([0, 1]))
    await g.reset()
    await g.step('offset_or_shell_geometry_script_mesh', mode='Shell', distance=5)
    await g.reset()
    await g.step('inset_outset_geometry_script_faces', distance=10, selected_triangles=[0, 1], expected_vertices=await g.tris([0, 1]))
    await g.reset()
    await g.step('bevel_geometry_script_polygroups', distance=5)
    await g.reset()
    await g.step('offset_geometry_script_faces', distance=10, selected_triangles=[0, 1], expected_vertices=await g.tris([0, 1]))
    await g.reset()
    await g.step('tessellate_geometry_script_mesh', level=2)
    await g.step('smooth_geometry_script_mesh', iterations=5, alpha=0.5)
    await g.step('apply_geometry_script_perlin_noise', magnitude=3, frequency=0.1, seed=7)
    await g.step('simplify_geometry_script_mesh', target_triangles=40)
    await g.step('remesh_geometry_script_mesh', target_triangles=300)
    await g.reset(shape='sphere')
    await g.step('warp_geometry_script_mesh', frame=frame(0), mode='Twist', angle_degrees=30, extent=60)
    await g.step('flare_geometry_script_mesh', frame=frame(0), percent_x=20, percent_y=20, extent=60)
    await g.step('wave_geometry_script_mesh', frame=frame(0), magnitude=4, frequency=0.05)
    await g.step('cut_geometry_script_mesh_with_plane', cut_frame=frame(0))
    await g.reset(shape='sphere')
    await g.step('model_geometry_script_mesh_with_plane', plane_frame=frame(0, x=20, rot={'X': 0, 'Y': 0.7071068, 'Z': 0, 'W': 0.7071068}), mode='Mirror')
    await g.step('self_union_geometry_script_mesh')
    await g.reset()
    await g.reset('Tool', 'sphere')
    src = {f'source_{k}': v for k, v in g.ident('Tool').items()}
    await g.step('boolean_geometry_script_meshes', operation='Subtract', **src)
    await g.step('append_geometry_script_mesh', **src)
    await g.step('remove_geometry_script_small_components', min_triangles=200)
    await g.step('copy_geometry_script_mesh', **src)
    await g.step('replace_geometry_script_mesh_with_convex_hull')
    await g.reset(shape='sphere')
    await g.step('replace_geometry_script_mesh_with_swept_hull', projection_frame=frame(0))
    # Native decomposition yields no hulls for one convex piece; two separate boxes decompose into two hulls.
    await g.reset()
    await g.call('append_geometry_script_box', {**g.ident('Target'), 'dimensions': {'X': 100, 'Y': 100, 'Z': 100}, 'transform': frame(0, x=150), 'confirm': True})
    await g.step('decompose_geometry_script_mesh_into_convex_hulls', hulls=2, check=lambda r: need(r['current_triangles'] == 24, r))
    await g.reset(shape='sphere')
    bad = await g.raw('decompose_geometry_script_mesh_into_convex_hulls', dict(g.ident('Target'), hulls=2, confirm=True))
    need('Hull Computation Failed' in str(bad), 'single convex piece', bad)

    # Collision on the Dynamic Mesh component.
    await g.reset()
    await g.step('generate_geometry_script_collision', method='MinVolumeShapes')
    await g.step('inspect_geometry_script_collision', check=lambda r: need(str(r).count('box') or r.get('shape_count') or r.get('total_shapes'), str(r)[:300]))
    await g.step('clear_geometry_script_collision')

    # Static Mesh round trip on a duplicated asset.
    await g.step('copy_static_mesh_to_geometry_script_mesh', comp='Tool', asset_path=SM)
    await g.reset(shape='sphere')
    await g.step('write_geometry_script_mesh_to_static_mesh', asset_path=SM, save=True)
    await g.step('generate_static_mesh_collision_from_geometry_script_mesh', asset_path=SM, save=True)
    await g.step('copy_static_mesh_to_geometry_script_mesh', comp='Tool', asset_path=SM)

    # Mode/method/type variants and selection-limited workflows.
    for method in ('FastMikkT', 'PerTriangle', 'StandardMikkT'):
        await g.reset()
        await g.step('compute_geometry_script_tangents', method=method, changes=False)
    for mode in ('PerVertex', 'PerFace', 'Repair'):
        await g.step('set_geometry_script_normal_mode', normal_mode=mode, changes=False)
    await g.reset()
    await g.call('generate_geometry_script_polygroups', {**g.ident('Target'), 'mode': 'Components', 'confirm': True})
    await g.step('split_geometry_script_normals', split_by_face_group=True, polygroup_layer=-1, changes=False)
    for mode in ('Components', 'UVIslands', 'Angle', 'Polygons'):
        await g.step('generate_geometry_script_polygroups', mode=mode, changes=False)
    # Alternate (extended) layer generation, summaries and region simplification on that layer.
    await g.step('set_geometry_script_polygroup_layer_count', layer_count=2, changes=False)
    await g.step('generate_geometry_script_polygroups', mode='Angle', polygroup_layer=1, changes=False)
    await g.step('inspect_geometry_script_polygroups', polygroup_layer=1, check=lambda r: need(r.get('groups') or r.get('group_count'), str(r)[:300]))
    await g.step('find_geometry_script_region_faces', filter_type='Polygroup', filter_id=0, polygroup_layer=1)
    await g.step('split_geometry_script_normals', split_by_face_group=True, polygroup_layer=1, changes=False)
    await g.step('simplify_geometry_script_regions', mode='Polygroups', polygroup_layer=1, changes=False)
    for proj in ('Planar', 'Box'):
        await g.reset()
        await g.step('project_geometry_script_uvs', transform=T0, projection=proj, changes=False)
    sel = [0, 1, 2, 3]
    await g.reset('Target', 'sphere')
    exp = await g.tris(sel)
    await g.step('project_geometry_script_uvs', transform=T0, projection='Planar', selected_triangles=sel, expected_vertices=exp, changes=False)
    await g.step('transform_geometry_script_uvs', scale_x=0.5, scale_y=0.5, selected_triangles=sel, expected_vertices=exp, changes=False)
    await g.step('recompute_geometry_script_uvs', selected_triangles=sel, expected_vertices=exp, changes=False)
    await g.step('scale_geometry_script_texel_density', mode='ApplyToWhole', selected_triangles=sel, expected_vertices=exp, changes=False)
    await g.step('smooth_geometry_script_mesh', iterations=3, alpha=0.5, selected_triangles=sel, expected_vertices=exp)
    await g.step('apply_geometry_script_perlin_noise', magnitude=3, selected_triangles=sel, expected_vertices=await g.tris(sel))
    bad = await g.raw('smooth_geometry_script_mesh', dict(g.ident('Target'), selected_triangles=sel, expected_vertices=[[0, 0, 0]] * 4, confirm=True))
    need('errorMessage' in bad, 'stale selection accepted')
    for mode in ('ApplyToIslands', 'ApplyToWhole', 'Normalize'):
        await g.step('scale_geometry_script_texel_density', mode=mode, changes=False)
    for method in ('SpectralConformal', 'ExpMap', 'Conformal'):
        await g.step('recompute_geometry_script_uvs', method=method, changes=False)
    for method in ('XAtlas', 'PatchBuilder'):
        await g.step('auto_generate_geometry_script_uvs', method=method, changes=False)
    for method in ('Automatic', 'MinimalFill', 'PolygonTriangulation', 'TriangleFan', 'PlanarProjection'):
        await g.reset()
        await g.call('delete_geometry_script_triangles', {**g.ident('Target'), 'selected_triangles': [0, 1], 'expected_vertices': await g.tris([0, 1]), 'confirm': True})
        # Fan/projection methods may add a centre vertex; the result must be closed.
        await g.step('fill_geometry_script_holes', method=method, check=lambda r: g.fp())
        f = await g.fp()
        need(f['closed'] and f['boundary_edges'] == 0, method, f)
    await g.reset()
    await g.step('repair_geometry_script_boundaries', mode='TJunctions', changes=False)
    for area in ('EntireSelection', 'PerPolygroup', 'PerTriangle'):
        await g.reset()
        await g.step('extrude_geometry_script_mesh', distance=10, area_mode=area, selected_triangles=[0, 1], expected_vertices=await g.tris([0, 1]))
    for direction in ('FixedDirection', 'AverageFaceNormal'):
        await g.reset()
        await g.step('extrude_geometry_script_mesh', distance=10, direction_mode=direction)
    for kind in ('VertexNormal', 'FaceNormal', 'ParallelFaceOffset'):
        await g.reset()
        await g.step('offset_geometry_script_faces', distance=10, offset_type=kind, selected_triangles=[0, 1], expected_vertices=await g.tris([0, 1]))
    for mode in ('Offset', 'Shell'):
        await g.reset('Target', 'sphere')
        await g.step('offset_or_shell_geometry_script_mesh', mode=mode, distance=4)
    await g.reset()
    await g.step('tessellate_geometry_script_mesh', method='PN', level=2)
    for method in ('AttributeAware', 'StandardQEM', 'VolumePreserving'):
        await g.reset('Target', 'sphere')
        await g.step('simplify_geometry_script_mesh', method=method, target_triangles=60)
    await g.reset('Target', 'sphere')
    await g.step('remesh_geometry_script_mesh', target_type='TargetEdgeLength', target_edge_length=15)
    for mode in ('Bend', 'Twist'):
        await g.reset('Target', 'sphere')
        await g.step('warp_geometry_script_mesh', frame=frame(0), mode=mode, angle_degrees=40, extent=60)
    for profile in ('Sin', 'SinSquared', 'Triangle'):
        await g.reset('Target', 'sphere')
        await g.step('flare_geometry_script_mesh', frame=frame(0), profile=profile, percent_x=30, percent_y=30, extent=60)
    for wave in ('SinWave1D', 'SinWave2D'):
        await g.reset('Target', 'sphere')
        await g.step('wave_geometry_script_mesh', frame=frame(0), wave_type=wave, magnitude=4, frequency=0.05)
    # Native ApplyMathWarpToMesh has no SinWave3D branch, so the route refuses it instead of reporting a silent no-op.
    bad = await g.raw('wave_geometry_script_mesh', dict(g.ident('Target'), frame=frame(0), wave_type='SinWave3D', confirm=True))
    need('SinWave3D' in str(bad.get('errorMessage', '')), bad)
    for op in ('Union', 'Intersection', 'Subtract', 'TrimInside', 'TrimOutside', 'NewPolyGroupInside', 'NewPolyGroupOutside'):
        await g.reset()
        await g.reset('Tool', 'sphere')
        await g.call('transform_geometry_script_mesh', {**g.ident('Tool'), 'transform': frame(80), 'confirm': True})
        await g.step('boolean_geometry_script_meshes', operation=op, changes=op not in ('NewPolyGroupInside', 'NewPolyGroupOutside'), **src)
    await g.step('copy_static_mesh_to_geometry_script_mesh', comp='Tool', asset_path='/Engine/BasicShapes/Cube.Cube', lod_type='RenderData')
    await g.step('copy_static_mesh_to_geometry_script_mesh', comp='Tool', asset_path='/Engine/BasicShapes/Cube.Cube', lod_type='SourceModel')

    # Final distinctive state for the cold restart.
    await g.reset()
    await g.call('tessellate_geometry_script_mesh', {**g.ident('Target'), 'level': 1, 'confirm': True})
    await g.call('set_geometry_script_material_ids', {**g.ident('Target'), 'material_id': 2, 'confirm': True})
    # Tool holds the sphere read back from the written Static Mesh asset.
    await g.call('copy_static_mesh_to_geometry_script_mesh', {**g.ident('Tool'), 'asset_path': SM, 'confirm': True})
    saved = httpx.post(BASE + '/worlds/save', json={'WorldPath': MAP, 'bConfirm': True}, timeout=600)
    if not saved.is_success:
        saved = httpx.post(BASE + '/editor/save-all', json={}, timeout=600)
    state = {'actor': g.actor, 'target': await g.fp('Target'), 'tool': await g.fp('Tool'),
             'target_topology': (await g.topo('Target', 32))['triangles'][:8]}
    covered = sorted(set(g.passed))
    all_geo = sorted(n for n in g.tools if 'geometry_script' in n)
    print(json.dumps({'failures': g.failures, 'untouched': sorted(set(all_geo) - set(covered) - {n for n, _ in g.failures})}, indent=1))
    print(f'{len(covered)} Geometry Script tools passed, {len({n for n, _ in g.failures})} failed, save status {saved.status_code}')
    assert not g.failures
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state, indent=1))


async def run_verify(api):
    g = Geo()
    g.tools = {t.name: t for t in await mcp_server.mcp.list_tools()}
    want = json.loads(STATE.read_text())
    g.actor = want['actor']
    assert api.call('POST', '/worlds/load', {'WorldPath': MAP, 'DirtyPolicy': 'discard', 'bConfirm': True})['success']
    got = {'actor': g.actor, 'target': await g.fp('Target'), 'tool': await g.fp('Tool'), 'target_topology': (await g.topo('Target', 32))['triangles'][:8]}
    assert json.loads(json.dumps(got)) == want, (got, want)
    # The written Static Mesh asset reloads with the sphere written into it.
    await g.call('copy_static_mesh_to_geometry_script_mesh', {**g.ident('Tool'), 'asset_path': SM, 'confirm': True})
    assert await g.fp('Tool') == want['tool']
    print('Target/Tool meshes and the written Static Mesh identical after cold reload')
    cleanup(api)


def cleanup(api):
    httpx.post(BASE + '/worlds/load', json={'WorldPath': '/Game/ThirdPerson/Lvl_ThirdPerson', 'DirtyPolicy': 'discard', 'bConfirm': True}, timeout=600)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': MAP}, timeout=180)
    httpx.post(BASE + '/assets/delete', json={'AssetPath': SM_PKG}, timeout=180)
    STATE.unlink(missing_ok=True)


if __name__ == '__main__':
    mcp_server.BASE_URL = BASE
    api = Api(BASE)
    cmd = COMMAND
    if cmd == 'prepare':
        asyncio.run(run_prepare(api))
    elif cmd == 'verify':
        asyncio.run(run_verify(api))
    else:
        cleanup(api)
