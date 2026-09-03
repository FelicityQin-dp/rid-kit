# Examples of RiD-kit
## Ala-dipeptide
```bash
rid submit -i ./ala2_input -c ./rid_json_files/rid_ala2.json -m machine_bohrium_k8s.json
```

## Chignolin
```bash
rid submit -i ./chignolin_input -c ./rid_json_files/rid_chignolin.json -m machine_bohrium_k8s.json
```

## Hafnium Oxide reaction
```bash
rid submit -i ./hfo2_input -c ./rid_json_files/rid_hfo2.json -m machine_bohrium_k8s.json
```

## LAMMPS custom-CV example
```bash
rid submit -i ./lj4_lmp_input -c ./rid_json_files/rid_lj4_lmp.json -m machine_bohrium_lmp_k8s.json
```
See `lj4_lmp_input/README.md` for LAMMPS input conventions and image requirements.