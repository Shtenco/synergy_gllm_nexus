from .contracts import EpistemicState
class RussianRenderer:
    def render(self,result):
        return {
            EpistemicState.PROVED:'Вывод подтверждён.',
            EpistemicState.DISPROVED:'Вывод опровергнут.',
            EpistemicState.UNRESOLVED:'Недостаточно данных для вывода.',
            EpistemicState.CONFLICTED:'Обнаружены противоречивые выводы.',
        }[result.state]
