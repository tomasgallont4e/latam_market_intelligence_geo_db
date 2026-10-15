/** Thin consumer adapter for the Peru map package. It never allocates national
 * workforce/persona counts to a district. Pass JSON documents loaded by caller. */
export function createPeruMapAdapter({catalog, indicators, personas, profiles, schoolGeoJSON, educationDistrictFacts=[]}) {
  if (catalog.country_code !== 'PE') throw new Error('Expected Peru map payload');
  const featureList = schoolGeoJSON?.features ?? [];
  const indicatorRows = indicators ?? [];
  const personaRows = personas ?? [];
  const profileRows = profiles ?? [];

  function countryMetrics(layer=null) {
    return indicatorRows.filter(x => x.scope_type === 'country' && x.scope_id === 'PE' && (!layer || x.layer === layer));
  }
  function persona(personaNumber) {
    const row=personaRows.find(x => x.group_type === 'persona' && String(x.persona_id).padStart(2,'0') === String(personaNumber).padStart(2,'0'));
    if (!row) return null;
    return {...row, local_count:null, local_count_status:'not_available_no_subnational_persona_estimates'};
  }
  function personaProfile(personaNumber) {
    const id=`P${String(personaNumber).padStart(2,'0')}`;
    return profileRows.filter(x => x.group_id === id && x.scope_id === 'PE');
  }
  function schoolPoints(ubigeo=null) {
    return featureList.filter(f => !ubigeo || f.properties?.ubigeo === String(ubigeo));
  }
  function districtEducation(ubigeo) {
    return educationDistrictFacts.filter(x => String(x.group_code ?? x.ubigeo) === String(ubigeo));
  }
  return {catalog,countryMetrics,persona,personaProfile,schoolPoints,districtEducation};
}
