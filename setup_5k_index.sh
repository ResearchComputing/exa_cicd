# Setup the index while specifying field/property
curl --insecure -u es_name:es_pass -X PUT "https://elastic1.rc.int.colorado.edu:9200/mfix-hcs-5k" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "_doc": {
      "properties": {
        "type": { "type": "keyword" },
        "job_nodes": { "type": "text" },
        "mfix_dat": { "type": "text" },
        "inputs": { "type": "text" },
        "image_url" : { "type" : "keyword" },
        "np": { "type": "integer" },
        "modules": { "type": "text" },
        "date": { "type": "date" },
        "jobnum": { "type": "keyword" },
        "git_commit_time": { "type": "date" },
        "git_commit_hash": { "type": "keyword" },
        "git_branch": { "type": "keyword" },
        "singularity_def_file": { "type": "text" },
        "walltime": { "type": "float" },
        "calc_particle_collisions()": { "type": "float" },
        "des_time_loop()": { "type": "float" },
        "FabArray::ParallelCopy()": { "type": "float" },
        "FillBoundary_finish()": { "type": "float" },
        "FillBoundary_nowait()": { "type": "float" },
        "MLNodeLaplacian::Fsmooth()": { "type": "float" },
        "MLNodeLaplacian::prepareForSolve()": { "type": "float" },
        "MLNodeLaplacian::restriction()" : { "type" : "float" },
        "MLEBABecLap::Fsmooth()": { "type": "float" },
        "mfix_dem::EvolveParticles_tstepadapt()": { "type": "float" },
        "mfix_dem::finderror()": { "type": "float" },
        "mfix_dem::EvolveParticles()": { "type": "float" },
        "NeighborParticleContainer::fillNeighborsMPI": { "type": "float" },
        "NeighborParticleContainer::getRcvCountsMPI": { "type": "float" },
        "NeighborParticleContainer::buildNeighborList": { "type": "float" },
        "NeighborParticleContainer::GetNeighborCommTags": { "type": "float" },
        "ParticleContainer::RedistributeMPI()": { "type": "float" }
      }
    }
  }
}
'

# Update index, adding fields
curl --insecure -u es_name:es_pass -X PUT "https://elastic1.rc.int.colorado.edu:9200/mfix-hcs-5k/_mapping/_doc" -H 'Content-Type: application/json' -d'
{
  "properties": {
    "image_url" : { "type" : "keyword" }
  }
}
'






###curl --insecure -u es_name:es_pass -X DELETE "https://elastic1.rc.int.colorado.edu:9200/mfix-hcs-5k"###







## fluid-bed index
# self.message['gas_fraction_image_url'] = self.gas_fraction_image_url
# self.message['velocity_image_url'] = self.velocity_image_url
# Setup the index while specifying field/property
curl --insecure -u es_name:es_pass -X PUT "https://elastic1.rc.int.colorado.edu:9200/mfix-fluid-bed" -H 'Content-Type: application/json' -d'
{
  "mappings": {
    "_doc": {
      "properties": {
        "type": { "type": "keyword" },
        "job_nodes": { "type": "text" },
        "mfix_dat": { "type": "text" },
        "inputs": { "type": "text" },
        "image_url" : { "type" : "keyword" },
        "np": { "type": "integer" },
        "modules": { "type": "text" },
        "date": { "type": "date" },
        "jobnum": { "type": "keyword" },
        "git_commit_time": { "type": "date" },
        "git_commit_hash": { "type": "keyword" },
        "git_branch": { "type": "keyword" },
        "singularity_def_file": { "type": "text" },
        "walltime": { "type": "float" },
        "gas_fraction_image_url" : { "type" : "keyword" },
        "velocity_image_url" : { "type" : "keyword" },
        "calc_particle_collisions()": { "type": "float" },
        "des_time_loop()": { "type": "float" },
        "FabArray::ParallelCopy()": { "type": "float" },
        "FillBoundary_finish()": { "type": "float" },
        "FillBoundary_nowait()": { "type": "float" },
        "MLNodeLaplacian::Fsmooth()": { "type": "float" },
        "MLNodeLaplacian::prepareForSolve()": { "type": "float" },
        "MLNodeLaplacian::restriction()" : { "type" : "float" },
        "MLEBABecLap::Fsmooth()": { "type": "float" },
        "mfix_dem::EvolveParticles_tstepadapt()": { "type": "float" },
        "mfix_dem::finderror()": { "type": "float" },
        "mfix_dem::EvolveParticles()": { "type": "float" },
        "NeighborParticleContainer::fillNeighborsMPI": { "type": "float" },
        "NeighborParticleContainer::getRcvCountsMPI": { "type": "float" },
        "NeighborParticleContainer::buildNeighborList": { "type": "float" },
        "NeighborParticleContainer::GetNeighborCommTags": { "type": "float" },
        "ParticleContainer::RedistributeMPI()": { "type": "float" }
      }
    }
  }
}
'

# Update index, adding fields
curl --insecure -u es_name:es_pass -X PUT "https://elastic1.rc.int.colorado.edu:9200/mfix-hcs-5k/_mapping/_doc" -H 'Content-Type: application/json' -d'
{
  "properties": {
    "image_url" : { "type" : "keyword" }
  }
}
'
