'use strict';
// Read-only map API (rule_map_api_readonly): only GET, only aggregates.
const express = require('express');
const data = require('../lib/mapData');
const cmp = require('../lib/compare');
const peru = require('../lib/peruData');

const router = express.Router();

const wrap = (fn) => async (req, res) => {
  try {
    res.json(await fn(req));
  } catch (e) {
    res.status(e.status || 500).json({ error: e.message });
  }
};

router.get('/api/map/departments', wrap((req) => data.getDepartments({ persona: req.query.persona })));
router.get('/api/map/municipalities', wrap((req) => data.getMunicipalities({ persona: req.query.persona })));
router.get('/api/map/localidades', wrap((req) => data.getLocalidades({ persona: req.query.persona })));
router.get('/api/personas', wrap(() => data.getPersonas()));
router.get('/api/peru/map', wrap(() => peru.getMap()));
router.get('/api/peru/departments', wrap(() => peru.getDepartmentMap()));
router.get('/api/peru/schools', wrap((req) => peru.getSchools(req.query)));
router.get('/api/peru/layers', wrap(() => peru.layerSummary()));
router.get('/api/compare/places', wrap((req) => cmp.listPlaces(req.query.level)));
router.get('/api/compare', wrap((req) => cmp.compare({ level: req.query.level, ids: req.query.ids, persona: req.query.persona })));

module.exports = router;
