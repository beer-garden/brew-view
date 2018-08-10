
/**
 * errorService - Service for displaying errors
 * @return {Object}      The service
 */
export default function errorService() {
  const errors = {
    noQueues: {
      problem: 'No Queues',
      description:
        "If no one has developed any plugins then there won't be any " +
        "queues here. You'll need to build and deploy some plugins.",
      resolution: 'Develop a Plugin',
    },
    requestRemoved: {
      problem: 'Request was removed',
      description: 'INFO-type requests are removed after several minutes',
      resolution: 'Go back to the list of all requests',
    },
    requestId: {
      problem: 'Incorrect ID',
      description: 'The ID does not refer to a valid request',
      resolution: 'Go back to the list of all requests',
    },
    systemId: {
      problem: "Incorrect ID",
      description:
        "The plugin was removed and reloaded which caused the ID to change",
      resolution: "Refresh the page",
    },
    noSystems: {
      problem: "No Systems",
      description:
        "If no one has developed any plugins then there won't be any " +
        "systems here. You'll need to build and deploy some plugins.",
      resolution: "Develop a Plugin",
    },
    dbMismatch: {
      problem: "Database Names Don't Match",
      description:
        "It's possible that the backend is pointing to a different " +
        "database than the frontend. Check to make sure that the " +
        "<code>db.name</code> is the same in both config files.",
      resolution:
        "<kbd>vim $APP_HOME/conf/bartender-config.yml</kbd><br />" +
        "<kbd>vim $APP_HOME/conf/brew-view-config.yml</kbd>",
    },
    unauthorized: {
      problem: "Not Logged In",
      description:
        "You're not logged in and anonymous users aren't able to view this " +
        "data or perform this action.",
      resolution:
        "Log in using the button at the top of the screen.",
    },
    forbidden: {
      problem: "Insufficient Permissions",
      description:
        "You don't have the necessary permission to view this data or " +
        "perform this action.",
      resolution:
        "Contact your administrator and request to be given permission.",
    },
  };

  const emptyMap = {
    queues: [
      errors.noQueues, errors.dbMismatch,
    ],
    request: [
      errors.requestId, errors.requestRemoved,
    ],
    system: [
      errors.systemId,
    ],
    systems: [
      errors.noSystems,
    ],
  };

  const errorMap = {
    401: [
      errors.unauthorized
    ],
    403: [
      errors.forbidden
    ],
  }

  return {
    empty: emptyMap,
    error: errorMap,
  };
};