// Clarifying-questions guidance for an estimate. Pure module: given the booking
// record and the prediction, it returns the questions / missing data that would
// sharpen the estimate, plus a confidence note.
//
// This is presentation/UX logic, deliberately OUTSIDE the API response (the
// Appendix A schema is locked to 7 fields). It runs in the validation UI and is
// unit-tested so the question logic stays correct.

import { extractScope, normalizeCategory } from './features.js';

const CATEGORY_QUESTIONS = {
  Plumbing: [
    'Is this a repair or a full replacement?',
    'Will you supply the parts and fixtures?',
    'How many fixtures or locations are affected?',
  ],
  Electrical: [
    'Is the wiring already in place, or does it need a new run?',
    'How many outlets, switches, or fixtures?',
    'Is a permit likely required?',
  ],
  HVAC: [
    'Is this a tune-up, a repair, or a full unit replacement?',
    'How many units, and roughly how old is the system?',
    'Do you know the system tonnage or model number?',
  ],
  Cleaning: [
    'How many rooms, or what square footage?',
    'One-time, or a recurring schedule?',
    'Any deep-clean areas (oven, fridge, interior windows)?',
  ],
  'Pest Control': [
    'Which pest are we treating?',
    'How large is the area (sq ft or number of bedrooms)?',
    'One-time treatment or an ongoing plan?',
  ],
  Landscaping: [
    'Roughly what is the yard size?',
    'One-time cleanup or recurring maintenance?',
    'Which tasks — mowing, trimming, mulch, planting?',
  ],
  Handyman: [
    'How many separate tasks are involved?',
    'Roughly how long do you expect it to take?',
    'Do you have the materials and parts on hand?',
  ],
  Painting: [
    'How many rooms, or what total square footage?',
    'Interior or exterior?',
    'Are you supplying the paint?',
  ],
  'Appliance Repair': [
    'Which appliance, and what brand/model?',
    'What symptoms are you seeing?',
    'Is it still under warranty?',
  ],
  Exterior: [
    'What surfaces, and roughly what area?',
    'Single-story or multi-story access?',
    'Any heavy stains or build-up to call out?',
  ],
  Roofing: [
    'Is this a repair or a full replacement?',
    'What roof material, and roughly what area?',
    'Are there any active leaks?',
  ],
  Moving: [
    'How many rooms, and how far is the move?',
    'Any large, heavy, or fragile items?',
    'Do you need packing help?',
  ],
};

const GENERIC_QUESTIONS = [
  'Roughly what size or quantity is involved?',
  'Will you supply the materials?',
  'Any access or scheduling constraints we should know about?',
];

const MAX_QUESTIONS = 4;
const THIN_DESCRIPTION_WORDS = 6;

function hasAnchorEstimate(record) {
  if (record.original_estimate !== undefined && record.original_estimate !== null) return true;
  return (
    record.original_estimate_lo !== undefined && record.original_estimate_lo !== null &&
    record.original_estimate_hi !== undefined && record.original_estimate_hi !== null
  );
}

export function clarifyingGuidance(record, prediction) {
  const category = normalizeCategory(record.service_category);
  const scope = extractScope(record.job_description);
  const questions = [];

  if (scope.desc_word_count < THIN_DESCRIPTION_WORDS) {
    questions.push('Can you describe the job in more detail — size, quantity, and materials?');
  }

  for (const question of CATEGORY_QUESTIONS[category] || GENERIC_QUESTIONS) {
    if (questions.length < MAX_QUESTIONS) questions.push(question);
  }

  if (!hasAnchorEstimate(record) && questions.length < MAX_QUESTIONS) {
    questions.push('Do you have a prior quote? Sharing it helps anchor the estimate.');
  }

  let note = null;
  if (prediction.confidence < 0.5) {
    note =
      'This job is outside our typical range, so the estimate is low-confidence and ' +
      'will be routed to a specialist to confirm before booking.';
  } else if (prediction.confidence < 0.75) {
    note = 'A few more details would tighten this estimate.';
  }

  return { questions: questions.slice(0, MAX_QUESTIONS), note };
}
