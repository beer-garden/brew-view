
commandService.$inject = ['$http', '$rootScope', 'SystemService'];

/**
 * commandService - Service for interacting with the command API.
 * @param  {$http} $http           Angular's $http Object.
 * @param  {$rootScope} $rootScope Angular's $rootScope Object.
 * @param  {Object} SystemService  Service for interacting with the system API.
 * @return {Object}               Service for interacting with the command API.
 */
export default function commandService($http, $rootScope, SystemService) {
  let CommandService = {};

  CommandService.getSystemName = function(command) {
    const system = CommandService.findSystem(command);
    return system.display_name || system.name;
  },

  CommandService.findSystem = function(command) {
    return $rootScope.findSystemByID(command.system.id);
  },

  CommandService.getStateParams = function(command) {
    let system = $rootScope.findSystemByID(command.system.id);
    return {
      systemName: system.name,
      systemVersion: $rootScope.getVersionForUrl(command.system),
      name: command.name,
      id: command.id,
    };
  },

  CommandService.getCommands = function() {
    return $http.get('api/v1/commands');
  },

  CommandService.getCommand = function(id) {
    return $http.get('api/v1/commands/' + id);
  },

  CommandService.comparison = function(a, b) {
    const aSystem = CommandService.getSystemName(a);
    const bSystem = CommandService.getSystemName(b);

    if (aSystem < bSystem) return -1;
    if (aSystem > bSystem) return 1;
    if (a.name < b.name) return -1;
    if (a.name > b.name) return 1;
    return 0;
  };

  return CommandService;
};
